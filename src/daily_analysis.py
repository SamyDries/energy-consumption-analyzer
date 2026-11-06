
import pandas as pd
from pathlib import Path

INPUT_PATH = Path("data/processed/household_power_consumption_clean.csv.gz")
OUTPUT_PATH = Path("results/daily_energy.csv")

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

print("=" * 55)
print("ENERGY CONSUMPTION ANALYZER")
print("DAILY ENERGY ANALYSIS")
print("=" * 55)

print("\nLoading prepared dataset...")

df = pd.read_csv(
    INPUT_PATH,
    compression="gzip",
    parse_dates=["datetime"]
)

print(f"Records loaded: {len(df):,}")

print("\nCalculating daily indicators...")

# Nombre de minutes présentes et nombre de mesures disponibles
daily = df.groupby(df["datetime"].dt.date).agg(
    expected_minutes=("Global_active_power", "size"),
    valid_minutes=("Global_active_power", "count"),
    power_sum=("Global_active_power", lambda x: x.sum(min_count=1)),
    mean_power_kw=("Global_active_power", "mean"),
    max_power_kw=("Global_active_power", "max")
)

daily.index.name = "date"
daily = daily.reset_index()

# Pourcentage de couverture des mesures
daily["coverage_pct"] = (
    daily["valid_minutes"] / daily["expected_minutes"] * 100
)

# Puissance en kW mesurée chaque minute :
# somme des valeurs / 60 = énergie observée en kWh
daily["observed_energy_kwh"] = daily["power_sum"] / 60

# Ne retenir l'énergie comme indicateur principal
# que lorsque la couverture atteint au moins 95 %
daily["energy_kwh"] = daily["observed_energy_kwh"].where(
    daily["coverage_pct"] >= 95
)

daily["date"] = daily["date"].astype(str)

# Sélection et ordre des colonnes finales
daily = daily[
    [
        "date",
        "expected_minutes",
        "valid_minutes",
        "coverage_pct",
        "observed_energy_kwh",
        "energy_kwh",
        "mean_power_kw",
        "max_power_kw"
    ]
]

print("\nSaving daily results...")
daily.to_csv(OUTPUT_PATH, index=False)

print("\n" + "=" * 55)
print("DAILY ANALYSIS COMPLETED")
print("=" * 55)

print(f"Number of days: {len(daily):,}")
print(
    "Days with at least 95% coverage:",
    int((daily["coverage_pct"] >= 95).sum())
)
print(
    "Days below 95% coverage:",
    int((daily["coverage_pct"] < 95).sum())
)
print(f"Average coverage: {daily['coverage_pct'].mean():.2f}%")

print("\nFirst 5 days:")
print(daily.head().to_string(index=False))

print(f"\nOutput file: {OUTPUT_PATH}")
