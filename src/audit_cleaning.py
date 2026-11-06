
import pandas as pd
from pathlib import Path

# --------------------------------------------------
# 1. PATHS
# --------------------------------------------------

DATA_PATH = Path("data/raw/household_power_consumption.txt")
REPORT_PATH = Path("results/cleaning_audit.txt")

REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------
# 2. LOAD ORIGINAL DATA
# --------------------------------------------------

print("Loading original UCI dataset...")

df = pd.read_csv(
    DATA_PATH,
    sep=";",
    na_values=["?"],
    low_memory=False
)

print("Dataset loaded successfully!")

# --------------------------------------------------
# 3. CONVERT DATE AND TIME
# --------------------------------------------------

df["datetime"] = pd.to_datetime(
    df["Date"] + " " + df["Time"],
    format="%d/%m/%Y %H:%M:%S",
    errors="coerce"
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

# --------------------------------------------------
# 4. DATA QUALITY AUDIT
# --------------------------------------------------

missing_values = df[numeric_cols].isna().sum()
missing_rows = df[numeric_cols].isna().all(axis=1).sum()

duplicate_rows = df.duplicated().sum()
duplicate_timestamps = df["datetime"].duplicated().sum()

invalid_dates = df["datetime"].isna().sum()

# Identify consecutive missing measurement periods
missing_mask = df[numeric_cols].isna().all(axis=1)

groups = missing_mask.ne(missing_mask.shift()).cumsum()

missing_runs = (
    df.loc[missing_mask]
    .groupby(groups[missing_mask])
    .size()
)

longest_missing_period = (
    int(missing_runs.max()) if not missing_runs.empty else 0
)

# Check time intervals
time_difference = df["datetime"].diff()

irregular_intervals = (
    time_difference.notna()
    & time_difference.ne(pd.Timedelta(minutes=1))
).sum()

# --------------------------------------------------
# 5. GENERATE REPORT
# --------------------------------------------------

report = f"""
==================================================
ENERGY CONSUMPTION ANALYZER
DATA QUALITY AUDIT
==================================================

1. DATASET INFORMATION

Rows: {len(df):,}
Columns: {len(df.columns)}
Memory: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB

2. DATETIME VALIDATION

Invalid timestamps: {invalid_dates:,}
Duplicate timestamps: {duplicate_timestamps:,}
Irregular time intervals: {irregular_intervals:,}

3. MISSING VALUES BY COLUMN

{missing_values.to_string()}

Total rows with all 7 measurements missing: {missing_rows:,}

4. CONSECUTIVE MISSING PERIODS

Number of missing periods: {len(missing_runs):,}
Longest missing period: {longest_missing_period:,} minutes

5. DUPLICATE RECORDS

Exact duplicate rows: {duplicate_rows:,}

==================================================
AUDIT COMPLETED
Original dataset was not modified.
==================================================
"""

print(report)

REPORT_PATH.write_text(report, encoding="utf-8")

print(f"\nReport saved to: {REPORT_PATH}")
