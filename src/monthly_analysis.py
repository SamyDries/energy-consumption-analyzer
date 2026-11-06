
import pandas as pd
from pathlib import Path

INPUT_PATH = Path("results/daily_energy.csv")
OUTPUT_PATH = Path("results/monthly_energy.csv")

print("=" * 55)
print("ENERGY CONSUMPTION ANALYZER")
print("MONTHLY ENERGY ANALYSIS")
print("=" * 55)

print("\nLoading daily results...")
df = pd.read_csv(INPUT_PATH, parse_dates=["date"])

print(f"Daily records loaded: {len(df):,}")

print("\nCalculating monthly indicators...")

df["month"] = df["date"].dt.to_period("M")

monthly = df.groupby("month").agg(
    expected_minutes=("expected_minutes", "sum"),
    valid_minutes=("valid_minutes", "sum"),
    observed_energy_kwh=("observed_energy_kwh", "sum"),
    mean_power_weighted=(
        "mean_power_kw",
        lambda x: 0
    ),
    max_power_kw=("max_power_kw", "max"),
    number_of_days=("date", "count")
).reset_index()

# Calculer la puissance moyenne pondérée par les minutes valides
weighted_power = (
    df.assign(
        weighted_power=df["mean_power_kw"] * df["valid_minutes"]
    )
    .groupby("month")
    .agg(
        total_weighted_power=("weighted_power", "sum"),
        total_valid_minutes=("valid_minutes", "sum")
    )
    .reset_index()
)

monthly = monthly.merge(weighted_power, on="month")

monthly["mean_power_kw"] = (
    monthly["total_weighted_power"] /
    monthly["total_valid_minutes"]
)

monthly["coverage_pct"] = (
    monthly["valid_minutes"] /
    monthly["expected_minutes"] * 100
)

# Ne publier le total mensuel comme indicateur fiable
# que si la couverture atteint 95 %
monthly["energy_kwh"] = monthly["observed_energy_kwh"].where(
    monthly["coverage_pct"] >= 95
)

monthly["month"] = monthly["month"].astype(str)

monthly = monthly[
    [
        "month",
        "number_of_days",
        "expected_minutes",
        "valid_minutes",
        "coverage_pct",
        "observed_energy_kwh",
        "energy_kwh",
        "mean_power_kw",
        "max_power_kw"
    ]
]

print("\nSaving monthly results...")
monthly.to_csv(OUTPUT_PATH, index=False)

print("\n" + "=" * 55)
print("MONTHLY ANALYSIS COMPLETED")
print("=" * 55)

print(f"Number of months: {len(monthly)}")
print(
    "Months with at least 95% coverage:",
    (monthly["coverage_pct"] >= 95).sum()
)
print(
    "Months below 95% coverage:",
    (monthly["coverage_pct"] < 95).sum()
)
print(
    f"Average monthly coverage: "
    f"{monthly['coverage_pct'].mean():.2f}%"
)

print("\nFirst 5 months:")
print(monthly.head().to_string(index=False))

print(f"\nOutput file: {OUTPUT_PATH}")
