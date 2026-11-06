
import pandas as pd
from pathlib import Path

INPUT_PATH = Path(
    "data/processed/household_power_consumption_clean.csv.gz"
)
OUTPUT_PATH = Path("results/hourly_energy.csv")

print("=" * 55)
print("ENERGY CONSUMPTION ANALYZER")
print("HOURLY ENERGY ANALYSIS")
print("=" * 55)

print("\nLoading prepared dataset...")
df = pd.read_csv(
    INPUT_PATH,
    compression="gzip",
    parse_dates=["datetime"]
)

print(f"Records loaded: {len(df):,}")

print("\nCalculating hourly indicators...")

df["hour"] = df["datetime"].dt.hour
df["date"] = df["datetime"].dt.date

hourly = df.groupby("hour").agg(
    expected_minutes=("Global_active_power", "size"),
    valid_minutes=("Global_active_power", "count"),
    observed_energy_kwh=(
        "Global_active_power",
        lambda x: x.sum() / 60
    ),
    mean_power_kw=("Global_active_power", "mean"),
    max_power_kw=("Global_active_power", "max"),
    number_of_days=("date", "nunique")
).reset_index()

hourly["coverage_pct"] = (
    hourly["valid_minutes"] /
    hourly["expected_minutes"] * 100
)

hourly["average_observed_energy_kwh_per_day"] = (
    hourly["observed_energy_kwh"] /
    hourly["number_of_days"]
)

# Conserver l'indicateur moyen uniquement si la couverture
# globale de cette heure atteint au moins 95 %.
hourly["average_energy_kwh_per_day"] = (
    hourly["average_observed_energy_kwh_per_day"].where(
        hourly["coverage_pct"] >= 95
    )
)

hourly["hour_label"] = hourly["hour"].apply(
    lambda h: f"{h:02d}:00"
)

hourly = hourly[
    [
        "hour",
        "hour_label",
        "number_of_days",
        "expected_minutes",
        "valid_minutes",
        "coverage_pct",
        "observed_energy_kwh",
        "average_observed_energy_kwh_per_day",
        "average_energy_kwh_per_day",
        "mean_power_kw",
        "max_power_kw"
    ]
]

hourly.to_csv(OUTPUT_PATH, index=False)

print("\n" + "=" * 55)
print("HOURLY ANALYSIS COMPLETED")
print("=" * 55)

print(f"Number of hourly groups: {len(hourly)}")
print(
    "Hours with at least 95% coverage:",
    (hourly["coverage_pct"] >= 95).sum()
)
print(
    "Hours below 95% coverage:",
    (hourly["coverage_pct"] < 95).sum()
)

print("\nHourly consumption profile:")
print(
    hourly[
        ["hour_label", "coverage_pct",
         "average_energy_kwh_per_day", "mean_power_kw"]
    ].to_string(index=False)
)

print(f"\nOutput file: {OUTPUT_PATH}")
