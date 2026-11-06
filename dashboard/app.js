
/* =========================================================
   ENERGY CONSUMPTION ANALYZER
   Professional Energy Monitoring Dashboard
   Data: UCI Individual Household Electric Power Consumption
========================================================= */

"use strict";

// ---------------------------------------------------------
// 1. CONFIGURATION
// ---------------------------------------------------------

const DATA_PATHS = {
    daily: "./data/daily.json",
    monthly: "./data/monthly.json",
    hourly: "./data/hourly.json"
};

const COLORS = {
    background: "#111c2e",
    text: "#e8eef7",
    muted: "#91a2b9",
    blue: "#38bdf8",
    violet: "#818cf8",
    green: "#34d399",
    orange: "#f59e0b",
    grid: "rgba(145, 162, 185, 0.12)"
};

const numberFormat = new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 2
});

const charts = {};

let dashboardData = {
    daily: [],
    monthly: [],
    hourly: []
};

let dailyPeriod = "all";


// ---------------------------------------------------------
// 2. GLOBAL CHART CONFIGURATION
// ---------------------------------------------------------

Chart.defaults.color = COLORS.muted;
Chart.defaults.font.family = "Arial, Helvetica, sans-serif";
Chart.defaults.font.size = 11;

Chart.defaults.plugins.legend.labels.usePointStyle = true;
Chart.defaults.plugins.legend.labels.padding = 18;

Chart.defaults.plugins.tooltip.backgroundColor = "#0b1120";
Chart.defaults.plugins.tooltip.titleColor = "#e8eef7";
Chart.defaults.plugins.tooltip.bodyColor = "#cbd5e1";
Chart.defaults.plugins.tooltip.borderColor = "#263750";
Chart.defaults.plugins.tooltip.borderWidth = 1;
Chart.defaults.plugins.tooltip.padding = 12;
Chart.defaults.plugins.tooltip.cornerRadius = 8;

const commonScales = {
    x: {
        grid: {
            display: false
        },
        border: {
            display: false
        },
        ticks: {
            maxRotation: 0,
            autoSkip: true,
            maxTicksLimit: 12
        }
    },

    y: {
        beginAtZero: true,
        grid: {
            color: COLORS.grid
        },
        border: {
            display: false,
            dash: [4, 4]
        },
        ticks: {
            padding: 10
        }
    }
};


// ---------------------------------------------------------
// 3. LOAD DATA
// ---------------------------------------------------------

async function loadDashboardData() {
    try {
        setStatus("Loading data...");

        const [dailyResponse, monthlyResponse, hourlyResponse] =
            await Promise.all([
                fetch(DATA_PATHS.daily),
                fetch(DATA_PATHS.monthly),
                fetch(DATA_PATHS.hourly)
            ]);

        if (
            !dailyResponse.ok ||
            !monthlyResponse.ok ||
            !hourlyResponse.ok
        ) {
            throw new Error("Unable to retrieve dashboard data.");
        }

        const [daily, monthly, hourly] = await Promise.all([
            dailyResponse.json(),
            monthlyResponse.json(),
            hourlyResponse.json()
        ]);

        if (
            !Array.isArray(daily) ||
            !Array.isArray(monthly) ||
            !Array.isArray(hourly) ||
            daily.length === 0 ||
            monthly.length === 0 ||
            hourly.length !== 24
        ) {
            throw new Error("Invalid or incomplete dataset.");
        }

        dashboardData = { daily, monthly, hourly };

        // Sort dates chronologically
        dashboardData.daily.sort(
            (a, b) => new Date(a.date) - new Date(b.date)
        );

        dashboardData.monthly.sort(
            (a, b) => a.month.localeCompare(b.month)
        );

        dashboardData.hourly.sort(
            (a, b) => a.hour - b.hour
        );

        setStatus("Dataset loaded successfully");

        updateKPIs();
        createDailyControls();
        renderDailyChart();
        renderMonthlyChart();
        renderHourlyChart();
        renderDataQualityChart();
        renderInsights();

    } catch (error) {
        console.error("Dashboard loading error:", error);

        setStatus("Data loading failed");

        const container = document.querySelector(".container");

        container.insertAdjacentHTML(
            "afterbegin",
            `
            <div class="error-message">
                <strong>Unable to load dashboard data.</strong>
                <p>${escapeHTML(error.message)}</p>
                <p>Check that the three JSON files exist in dashboard/data/.</p>
            </div>
            `
        );
    }
}


// ---------------------------------------------------------
// 4. STATUS
// ---------------------------------------------------------

function setStatus(message) {
    const status = document.getElementById("data-status");

    if (status) {
        status.textContent = message;
    }
}


// ---------------------------------------------------------
// 5. KPI CALCULATIONS
// ---------------------------------------------------------

function updateKPIs() {
    const daily = dashboardData.daily;

    const reliableDays = daily.filter(
        row =>
            Number(row.coverage_pct) >= 95 &&
            Number.isFinite(Number(row.energy_kwh))
    );

    const totalEnergy = reliableDays.reduce(
        (sum, row) => sum + Number(row.energy_kwh),
        0
    );

    const averageDaily = reliableDays.length
        ? totalEnergy / reliableDays.length
        : 0;

    // Weighted average power across all valid measurements
    const validMinutes = daily.reduce(
        (sum, row) => sum + Number(row.valid_minutes || 0),
        0
    );

    const weightedPower = daily.reduce(
        (sum, row) =>
            sum +
            Number(row.mean_power_kw || 0) *
            Number(row.valid_minutes || 0),
        0
    );

    const averagePower = validMinutes
        ? weightedPower / validMinutes
        : 0;

    // Overall coverage, weighted by expected minutes
    const expectedMinutes = daily.reduce(
        (sum, row) => sum + Number(row.expected_minutes || 0),
        0
    );

    const overallCoverage = expectedMinutes
        ? validMinutes / expectedMinutes * 100
        : 0;

    setText(
        "total-energy",
        `${numberFormat.format(totalEnergy / 1000)} MWh`
    );

    setText(
        "average-daily",
        `${numberFormat.format(averageDaily)} kWh`
    );

    setText(
        "average-power",
        `${numberFormat.format(averagePower)} kW`
    );

    setText(
        "data-coverage",
        `${overallCoverage.toFixed(2)}%`
    );

    // Add reliable day information
    const totalDescription = document.querySelector(
        "#total-energy"
    )?.parentElement?.querySelector(".kpi-description");

    if (totalDescription) {
        totalDescription.textContent =
            `${reliableDays.length.toLocaleString("en-US")} reliable days (≥95% coverage)`;
    }

    const coverageDescription = document.querySelector(
        "#data-coverage"
    )?.parentElement?.querySelector(".kpi-description");

    if (coverageDescription) {
        coverageDescription.textContent =
            `${validMinutes.toLocaleString("en-US")} valid measurements`;
    }
}


// ---------------------------------------------------------
// 6. DAILY PERIOD FILTER
// ---------------------------------------------------------

function createDailyControls() {
    const heading = document.querySelector(
        "#dailyChart"
    )?.closest(".chart-section")?.querySelector(".section-heading");

    if (!heading || heading.querySelector(".period-controls")) {
        return;
    }

    const controls = document.createElement("div");

    controls.className = "period-controls";

    controls.innerHTML = `
        <button class="period-button" data-period="30">30D</button>
        <button class="period-button" data-period="90">90D</button>
        <button class="period-button" data-period="365">1Y</button>
        <button class="period-button active" data-period="all">ALL</button>
    `;

    heading.appendChild(controls);

    controls.addEventListener("click", event => {
        const button = event.target.closest("[data-period]");

        if (!button) return;

        dailyPeriod = button.dataset.period;

        controls.querySelectorAll("button").forEach(item => {
            item.classList.toggle("active", item === button);
        });

        renderDailyChart();
    });
}


// ---------------------------------------------------------
// 7. DAILY CONSUMPTION CHART
// ---------------------------------------------------------

function renderDailyChart() {
    const canvas = document.getElementById("dailyChart");

    if (!canvas) return;

    let data = [...dashboardData.daily];

    if (dailyPeriod !== "all") {
        const days = Number(dailyPeriod);

        data = data.slice(-days);
    }

    const context = canvas.getContext("2d");

    const gradient = context.createLinearGradient(
        0, 0, 0, 350
    );

    gradient.addColorStop(0, "rgba(56, 189, 248, 0.28)");
    gradient.addColorStop(1, "rgba(56, 189, 248, 0.00)");

    createChart("daily", canvas, {
        type: "line",

        data: {
            labels: data.map(row => row.date),

            datasets: [{
                label: "Daily energy",
                data: data.map(row => row.energy_kwh),
                borderColor: COLORS.blue,
                backgroundColor: gradient,
                fill: true,
                borderWidth: 1.5,
                pointRadius: 0,
                pointHoverRadius: 4,
                tension: 0.15,
                spanGaps: false
            }]
        },

        options: {
            ...baseChartOptions(),

            interaction: {
                intersect: false,
                mode: "index"
            },

            plugins: {
                ...baseChartOptions().plugins,

                tooltip: {
                    ...Chart.defaults.plugins.tooltip,

                    callbacks: {
                        label: context => {
                            const value = context.parsed.y;

                            return value === null
                                ? "Energy: unavailable (insufficient coverage)"
                                : `Energy: ${numberFormat.format(value)} kWh`;
                        }
                    }
                }
            },

            scales: {
                ...commonScales,

                y: {
                    ...commonScales.y,
                    title: {
                        display: true,
                        text: "Energy (kWh)"
                    }
                }
            }
        }
    });
}


// ---------------------------------------------------------
// 8. MONTHLY CONSUMPTION CHART
// ---------------------------------------------------------

function renderMonthlyChart() {
    const canvas = document.getElementById("monthlyChart");

    if (!canvas) return;

    const data = dashboardData.monthly;

    createChart("monthly", canvas, {
        type: "bar",

        data: {
            labels: data.map(row => row.month),

            datasets: [{
                label: "Monthly energy",
                data: data.map(row => row.energy_kwh),
                backgroundColor: data.map(row =>
                    Number(row.coverage_pct) >= 95
                        ? "rgba(129, 140, 248, 0.75)"
                        : "rgba(245, 158, 11, 0.30)"
                ),
                borderColor: data.map(row =>
                    Number(row.coverage_pct) >= 95
                        ? COLORS.violet
                        : COLORS.orange
                ),
                borderWidth: 1,
                borderRadius: 4,
                maxBarThickness: 24
            }]
        },

        options: {
            ...baseChartOptions(),

            plugins: {
                ...baseChartOptions().plugins,

                tooltip: {
                    ...Chart.defaults.plugins.tooltip,

                    callbacks: {
                        label: context => {
                            const row = data[context.dataIndex];

                            return row.energy_kwh === null
                                ? "Energy: unavailable (coverage below 95%)"
                                : `Energy: ${numberFormat.format(row.energy_kwh)} kWh`;
                        },

                        afterLabel: context => {
                            const row = data[context.dataIndex];

                            return `Data coverage: ${Number(row.coverage_pct).toFixed(2)}%`;
                        }
                    }
                }
            },

            scales: {
                ...commonScales,

                x: {
                    ...commonScales.x,

                    ticks: {
                        ...commonScales.x.ticks,
                        maxTicksLimit: 16
                    }
                },

                y: {
                    ...commonScales.y,

                    title: {
                        display: true,
                        text: "Energy (kWh)"
                    }
                }
            }
        }
    });
}


// ---------------------------------------------------------
// 9. HOURLY CONSUMPTION PROFILE
// ---------------------------------------------------------

function renderHourlyChart() {
    const canvas = document.getElementById("hourlyChart");

    if (!canvas) return;

    const data = dashboardData.hourly;

    const values = data.map(
        row => row.average_energy_kwh_per_day
    );

    const peakIndex = values.reduce(
        (maxIndex, value, index) =>
            value > values[maxIndex] ? index : maxIndex,
        0
    );

    const colors = values.map((value, index) =>
        index === peakIndex
            ? COLORS.green
            : "rgba(56, 189, 248, 0.65)"
    );

    createChart("hourly", canvas, {
        type: "bar",

        data: {
            labels: data.map(row => row.hour_label),

            datasets: [{
                label: "Average energy per day",
                data: values,
                backgroundColor: colors,
                borderRadius: 5,
                maxBarThickness: 30
            }]
        },

        options: {
            ...baseChartOptions(),

            plugins: {
                ...baseChartOptions().plugins,

                tooltip: {
                    ...Chart.defaults.plugins.tooltip,

                    callbacks: {
                        label: context =>
                            `Average: ${numberFormat.format(context.parsed.y)} kWh`
                    }
                }
            },

            scales: {
                ...commonScales,

                y: {
                    ...commonScales.y,

                    title: {
                        display: true,
                        text: "Average energy (kWh)"
                    }
                }
            }
        }
    });
}


// ---------------------------------------------------------
// 10. DATA QUALITY CHART
// ---------------------------------------------------------

function renderDataQualityChart() {
    const originalSection = document.querySelector(
        "#hourlyChart"
    )?.closest(".chart-section");

    if (!originalSection) return;

    const section = document.createElement("section");

    section.className = "chart-section";

    section.innerHTML = `
        <div class="section-heading">
            <div>
                <p class="eyebrow">DATA QUALITY</p>
                <h2>Measurement Coverage</h2>
            </div>

            <span class="unit-label">Percentage (%)</span>
        </div>

        <div class="chart-card">
            <canvas id="qualityChart"></canvas>
        </div>
    `;

    originalSection.after(section);

    const canvas = document.getElementById("qualityChart");

    createChart("quality", canvas, {
        type: "line",

        data: {
            labels: dashboardData.daily.map(row => row.date),

            datasets: [{
                label: "Daily coverage",
                data: dashboardData.daily.map(
                    row => row.coverage_pct
                ),
                borderColor: COLORS.green,
                backgroundColor: "rgba(52, 211, 153, 0.08)",
                fill: true,
                borderWidth: 1.5,
                pointRadius: 0,
                tension: 0,
                spanGaps: false
            }]
        },

        options: {
            ...baseChartOptions(),

            plugins: {
                ...baseChartOptions().plugins,

                annotation: undefined,

                tooltip: {
                    ...Chart.defaults.plugins.tooltip,

                    callbacks: {
                        label: context =>
                            `Coverage: ${Number(context.parsed.y).toFixed(2)}%`
                    }
                }
            },

            scales: {
                ...commonScales,

                y: {
                    ...commonScales.y,
                    min: 0,
                    max: 100,

                    title: {
                        display: true,
                        text: "Coverage (%)"
                    }
                }
            }
        },

        plugins: [{
            id: "coverageThreshold",

            afterDraw(chart) {
                const { ctx, chartArea, scales } = chart;

                if (!chartArea) return;

                const y = scales.y.getPixelForValue(95);

                ctx.save();

                ctx.beginPath();
                ctx.setLineDash([6, 5]);
                ctx.strokeStyle = COLORS.orange;
                ctx.lineWidth = 1.5;

                ctx.moveTo(chartArea.left, y);
                ctx.lineTo(chartArea.right, y);

                ctx.stroke();

                ctx.fillStyle = COLORS.orange;
                ctx.font = "11px Arial";
                ctx.fillText("95% threshold", chartArea.right - 90, y - 7);

                ctx.restore();
            }
        }]
    });
}


// ---------------------------------------------------------
// 11. AUTOMATIC INSIGHTS
// ---------------------------------------------------------

function renderInsights() {
    const daily = dashboardData.daily;
    const hourly = dashboardData.hourly;

    const reliableDays = daily.filter(
        row =>
            Number(row.coverage_pct) >= 95 &&
            Number.isFinite(Number(row.energy_kwh))
    );

    const peakHour = hourly.reduce(
        (best, row) =>
            Number(row.average_energy_kwh_per_day) >
            Number(best.average_energy_kwh_per_day)
                ? row
                : best,
        hourly[0]
    );

    const lowestHour = hourly.reduce(
        (best, row) =>
            Number(row.average_energy_kwh_per_day) <
            Number(best.average_energy_kwh_per_day)
                ? row
                : best,
        hourly[0]
    );

    const highestDay = reliableDays.reduce(
        (best, row) =>
            Number(row.energy_kwh) > Number(best.energy_kwh)
                ? row
                : best,
        reliableDays[0]
    );

    const lowestDay = reliableDays.reduce(
        (best, row) =>
            Number(row.energy_kwh) < Number(best.energy_kwh)
                ? row
                : best,
        reliableDays[0]
    );

    const insights = document.createElement("section");

    insights.className = "chart-section insights-section";

    insights.innerHTML = `
        <div class="section-heading">
            <div>
                <p class="eyebrow">ANALYTICAL SUMMARY</p>
                <h2>Consumption Highlights</h2>
            </div>
        </div>

        <div class="insights-grid">

            <article class="insight-card">
                <span class="insight-label">Peak consumption hour</span>
                <strong>${escapeHTML(peakHour.hour_label)}</strong>
                <p>
                    ${numberFormat.format(
                        peakHour.average_energy_kwh_per_day
                    )} kWh average per day
                </p>
            </article>

            <article class="insight-card">
                <span class="insight-label">Lowest consumption hour</span>
                <strong>${escapeHTML(lowestHour.hour_label)}</strong>
                <p>
                    ${numberFormat.format(
                        lowestHour.average_energy_kwh_per_day
                    )} kWh average per day
                </p>
            </article>

            <article class="insight-card">
                <span class="insight-label">Highest reliable day</span>
                <strong>${numberFormat.format(highestDay.energy_kwh)} kWh</strong>
                <p>${escapeHTML(highestDay.date)}</p>
            </article>

            <article class="insight-card">
                <span class="insight-label">Lowest reliable day</span>
                <strong>${numberFormat.format(lowestDay.energy_kwh)} kWh</strong>
                <p>${escapeHTML(lowestDay.date)}</p>
            </article>

        </div>

        <p class="methodology-note">
            Daily energy indicators are displayed only when measurement
            coverage is at least 95%. Missing measurements are not
            interpreted as zero consumption.
        </p>
    `;

    const qualitySection = document.getElementById("qualityChart")
        ?.closest(".chart-section");

    if (qualitySection) {
        qualitySection.after(insights);
    }
}


// ---------------------------------------------------------
// 12. CHART FACTORY
// ---------------------------------------------------------

function createChart(name, canvas, config) {
    if (charts[name]) {
        charts[name].destroy();
    }

    charts[name] = new Chart(canvas, config);
}

function baseChartOptions() {
    return {
        responsive: true,
        maintainAspectRatio: false,

        animation: {
            duration: 500
        },

        plugins: {
            legend: {
                display: false
            },

            tooltip: {
                enabled: true
            }
        }
    };
}


// ---------------------------------------------------------
// 13. SMALL UTILITIES
// ---------------------------------------------------------

function setText(id, value) {
    const element = document.getElementById(id);

    if (element) {
        element.textContent = value;
    }
}

function escapeHTML(value) {
    return String(value).replace(/[&<>"']/g, character => {
        const entities = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;"
        };

        return entities[character];
    });
}


// ---------------------------------------------------------
// 14. ADDITIONAL INTERFACE STYLES
// ---------------------------------------------------------

function addDashboardStyles() {
    const style = document.createElement("style");

    style.textContent = `
        .chart-card {
            height: 390px;
        }

        .period-controls {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            background: #0b1120;
            border: 1px solid #263750;
            padding: 4px;
            border-radius: 7px;
        }

        .period-button {
            background: transparent;
            color: #91a2b9;
            border: none;
            padding: 7px 12px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 11px;
            font-weight: 600;
            transition: 0.2s;
        }

        .period-button:hover {
            color: #e8eef7;
            background: #17243a;
        }

        .period-button.active {
            background: #263750;
            color: #38bdf8;
        }

        .insights-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
        }

        .insight-card {
            background: #111c2e;
            border: 1px solid #263750;
            border-radius: 10px;
            padding: 20px;
        }

        .insight-label {
            display: block;
            color: #91a2b9;
            font-size: 11px;
            margin-bottom: 12px;
        }

        .insight-card strong {
            display: block;
            font-size: 23px;
            color: #e8eef7;
            margin-bottom: 6px;
        }

        .insight-card p {
            color: #91a2b9;
            font-size: 12px;
        }

        .methodology-note {
            margin-top: 16px;
            color: #91a2b9;
            font-size: 12px;
            line-height: 1.7;
        }

        .error-message {
            background: rgba(245, 158, 11, 0.08);
            border: 1px solid rgba(245, 158, 11, 0.4);
            color: #fbbf24;
            border-radius: 8px;
            padding: 18px;
            margin-bottom: 25px;
        }

        .error-message p {
            margin-top: 7px;
            font-size: 13px;
        }

        @media (max-width: 1000px) {
            .insights-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }

        @media (max-width: 650px) {
            .chart-card {
                height: 310px;
            }

            .insights-grid {
                grid-template-columns: 1fr;
            }

            .period-controls {
                width: 100%;
                justify-content: space-between;
            }

            .period-button {
                flex: 1;
                padding: 7px 8px;
            }
        }
    `;

    document.head.appendChild(style);
}


// ---------------------------------------------------------
// 15. INITIALIZE DASHBOARD
// ---------------------------------------------------------

document.addEventListener("DOMContentLoaded", () => {
    addDashboardStyles();
    loadDashboardData();
});
