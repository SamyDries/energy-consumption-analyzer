
import pandas as pd
from pathlib import Path

# ==========================================
# 1. PROJECT PATHS
# ==========================================

INPUT_PATH = Path("data/raw/household_power_consumption.txt")
OUTPUT_PATH = Path(
    "data/processed/household_power_consumption_clean.csv.gz"
)

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

# ==========================================
# 2. LOAD ORIGINAL DATA
# ==========================================

print("=" * 55)
print("ENERGY CONSUMPTION ANALYZER")
print("DATA PREPARATION")
print("=" * 55)

print("\nLoading original dataset...")

df = pd.read_csv(
    INPUT_PATH,
    sep=";",
    na_values=["?"],
    low_memory=False
)

print(f"Original records: {len(df):,}")

# ==========================================
# 3. CREATE DATETIME COLUMN
# ==========================================

print("\nConverting Date and Time...")

df["datetime"] = pd.to_datetime(
    df["Date"] + " " + df["Time"],
    format="%d/%m/%Y %H:%M:%S",
    errors="coerce"
)

# ==========================================
# 4. SELECT ANALYSIS COLUMNS
# ==========================================

numeric_cols = [
    "Global_active_power",
    "Global_reactive_power",
    "Voltage",
    "Global_intensity",
    "Sub_metering_1",
    "Sub_metering_2",
    "Sub_metering_3"
]

df = df[["datetime"] + numeric_cols].copy()

# ==========================================
# 5. DATA VALIDATION
# ==========================================

print("\nValidating prepared data...")

assert df["datetime"].notna().all(), "Invalid datetime detected!"

assert df["datetime"].is_monotonic_increasing, (
    "Dataset is not chronologically sorted!"
)

missing_rows = df[numeric_cols].isna().all(axis=1).sum()

assert missing_rows == 25979, (
    "Unexpected number of missing measurement rows!"
)

# ==========================================
# 6. PRESERVE MISSING VALUES
# ==========================================

print("\nMissing values will be preserved.")
print(f"Rows with missing measurements: {missing_rows:,}")

# ==========================================
# 7. SAVE COMPRESSED DATASET
# ==========================================

print("\nSaving cleaned dataset...")

df.to_csv(
    OUTPUT_PATH,
    index=False,
    compression="gzip",
    date_format="%Y-%m-%d %H:%M:%S"
)

# ==========================================
# 8. FINAL REPORT
# ==========================================

file_size = OUTPUT_PATH.stat().st_size / (1024 ** 2)

print("\n" + "=" * 55)
print("DATA PREPARATION COMPLETED")
print("=" * 55)

print(f"Total records: {len(df):,}")
print(f"Total columns: {len(df.columns)}")
print(f"Missing measurement rows: {missing_rows:,}")
print(f"Missing percentage: {missing_rows / len(df) * 100:.2f}%")
print(f"Compressed file size: {file_size:.2f} MB")
print(f"Output: {OUTPUT_PATH}")

print("\nOriginal dataset remains unchanged.")
