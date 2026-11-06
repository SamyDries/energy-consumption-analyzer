
import pandas as pd
from pathlib import Path

# Paths
DATA_PATH = Path("data/raw/household_power_consumption.txt")
OUTPUT_PATH = Path("results/missing_periods.csv")

# Load dataset
print("Loading dataset...")

df = pd.read_csv(
    DATA_PATH,
    sep=";",
    na_values=["?"],
    low_memory=False
)

# Convert datetime
df["datetime"] = pd.to_datetime(
    df["Date"] + " " + df["Time"],
    format="%d/%m/%Y %H:%M:%S"
)

numeric_cols = [
    "Global_active_power",
    "Global_reactive_power",
    "Voltage",
    "Global_intensity",
    "Sub_metering_1",
    "Sub_metering_2",
    "Sub_metering_3"
]

# Identify rows where all measurements are missing
missing_mask = df[numeric_cols].isna().all(axis=1)

# Group consecutive missing rows
groups = missing_mask.ne(missing_mask.shift()).cumsum()

missing_data = df.loc[missing_mask, ["datetime"]].copy()
missing_data["group"] = groups[missing_mask]

# Summarize each missing period
periods = (
    missing_data.groupby("group")
    .agg(
        start_datetime=("datetime", "min"),
        end_datetime=("datetime", "max"),
        duration_minutes=("datetime", "size")
    )
    .reset_index(drop=True)
)

periods["duration_hours"] = (
    periods["duration_minutes"] / 60
).round(2)

# Sort longest periods first
periods = periods.sort_values(
    "duration_minutes",
    ascending=False
)

# Save results
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
periods.to_csv(OUTPUT_PATH, index=False)

# Display results
print("\nMISSING PERIODS ANALYSIS")
print("=" * 60)

print(f"Total missing periods: {len(periods)}")

print("\nTop 10 longest missing periods:")
print(periods.head(10).to_string(index=False))

print("\nSummary:")
print(periods["duration_minutes"].describe())

print(f"\nResults saved to: {OUTPUT_PATH}")
print("\nAnalysis completed!")

