
import pandas as pd
from pathlib import Path

# Fichiers sources
FILES = {
    "daily": "results/daily_energy.csv",
    "monthly": "results/monthly_energy.csv",
    "hourly": "results/hourly_energy.csv"
}

# Dossier de destination
OUTPUT_DIR = Path("dashboard/data")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 55)
print("ENERGY CONSUMPTION ANALYZER")
print("DASHBOARD DATA EXPORT")
print("=" * 55)

for name, input_file in FILES.items():

    print(f"\nProcessing {name} data...")

    df = pd.read_csv(input_file)

    output_file = OUTPUT_DIR / f"{name}.json"

    # NaN devient null dans le JSON.
    # Les dates et les valeurs numériques sont conservées.
    df.to_json(
        output_file,
        orient="records",
        indent=2,
        force_ascii=False,
        double_precision=6
    )

    size_kb = output_file.stat().st_size / 1024

    print(f"Records exported: {len(df):,}")
    print(f"Output: {output_file}")
    print(f"File size: {size_kb:.2f} KB")

print("\n" + "=" * 55)
print("DASHBOARD DATA EXPORT COMPLETED")
print("=" * 55)

print("\nGenerated files:")

for file in OUTPUT_DIR.glob("*.json"):
    print(f"{file.name}: {file.stat().st_size:,} bytes")
