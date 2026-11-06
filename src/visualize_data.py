
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Fichiers sources
DAILY_FILE = Path("results/daily_energy.csv")
MONTHLY_FILE = Path("results/monthly_energy.csv")
HOURLY_FILE = Path("results/hourly_energy.csv")

# Dossier de sauvegarde
OUTPUT_DIR = Path("results/figures")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 55)
print("ENERGY CONSUMPTION ANALYZER")
print("MATPLOTLIB VISUALIZATIONS")
print("=" * 55)

# Chargement des données
print("\nLoading analysis results...")

daily = pd.read_csv(DAILY_FILE, parse_dates=["date"])
monthly = pd.read_csv(MONTHLY_FILE)
hourly = pd.read_csv(HOURLY_FILE)

print(f"Daily records: {len(daily):,}")
print(f"Monthly records: {len(monthly):,}")
print(f"Hourly records: {len(hourly):,}")


# --------------------------------------------------
# 1. DAILY ENERGY CONSUMPTION
# --------------------------------------------------

print("\nGenerating daily consumption chart...")

fig, ax = plt.subplots(figsize=(14, 6))

ax.plot(
    daily["date"],
    daily["energy_kwh"],
    linewidth=0.8
)

ax.set_title(
    "Daily Household Energy Consumption",
    fontsize=15,
    fontweight="bold"
)
ax.set_xlabel("Date")
ax.set_ylabel("Energy Consumption (kWh)")
ax.grid(True, alpha=0.3)

fig.autofmt_xdate()
fig.tight_layout()

fig.savefig(
    OUTPUT_DIR / "daily_consumption.png",
    dpi=200,
    bbox_inches="tight"
)
plt.close(fig)


# --------------------------------------------------
# 2. MONTHLY ENERGY CONSUMPTION
# --------------------------------------------------

print("Generating monthly consumption chart...")

monthly["month_date"] = pd.to_datetime(monthly["month"])

fig, ax = plt.subplots(figsize=(14, 6))

ax.bar(
    monthly["month_date"],
    monthly["energy_kwh"],
    width=20
)

ax.set_title(
    "Monthly Household Energy Consumption",
    fontsize=15,
    fontweight="bold"
)
ax.set_xlabel("Month")
ax.set_ylabel("Energy Consumption (kWh)")
ax.grid(axis="y", alpha=0.3)

fig.autofmt_xdate()
fig.tight_layout()

fig.savefig(
    OUTPUT_DIR / "monthly_consumption.png",
    dpi=200,
    bbox_inches="tight"
)
plt.close(fig)


# --------------------------------------------------
# 3. HOURLY CONSUMPTION PROFILE
# --------------------------------------------------

print("Generating hourly consumption chart...")

fig, ax = plt.subplots(figsize=(12, 6))

ax.bar(
    hourly["hour_label"],
    hourly["average_energy_kwh_per_day"]
)

ax.set_title(
    "Average Daily Energy Consumption by Hour",
    fontsize=15,
    fontweight="bold"
)
ax.set_xlabel("Hour of the Day")
ax.set_ylabel("Average Energy (kWh per hour)")
ax.grid(axis="y", alpha=0.3)

ax.tick_params(axis="x", rotation=45)

fig.tight_layout()

fig.savefig(
    OUTPUT_DIR / "hourly_consumption.png",
    dpi=200,
    bbox_inches="tight"
)
plt.close(fig)


# --------------------------------------------------
# 4. DAILY DATA COVERAGE
# --------------------------------------------------

print("Generating data coverage chart...")

fig, ax = plt.subplots(figsize=(14, 6))

ax.plot(
    daily["date"],
    daily["coverage_pct"],
    linewidth=0.9
)

ax.axhline(
    y=95,
    linestyle="--",
    linewidth=1.5,
    label="95% coverage threshold"
)

ax.set_title(
    "Daily Data Coverage",
    fontsize=15,
    fontweight="bold"
)
ax.set_xlabel("Date")
ax.set_ylabel("Data Coverage (%)")
ax.set_ylim(0, 105)
ax.legend()
ax.grid(True, alpha=0.3)

fig.autofmt_xdate()
fig.tight_layout()

fig.savefig(
    OUTPUT_DIR / "daily_data_coverage.png",
    dpi=200,
    bbox_inches="tight"
)
plt.close(fig)


# --------------------------------------------------
# SUMMARY
# --------------------------------------------------

print("\n" + "=" * 55)
print("VISUALIZATION COMPLETED")
print("=" * 55)

print("\nGenerated figures:")

for file in sorted(OUTPUT_DIR.glob("*.png")):
    size_kb = file.stat().st_size / 1024
    print(f"{file.name}: {size_kb:.2f} KB")

print(f"\nOutput directory: {OUTPUT_DIR}")
