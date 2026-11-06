
import pandas as pd
from pathlib import Path

# Dataset location
DATA_PATH = Path("data/raw/household_power_consumption.txt")

print("=" * 60)
print("ENERGY CONSUMPTION ANALYZER")
print("=" * 60)

# Load the real UCI dataset
df = pd.read_csv(
    DATA_PATH,
    sep=";",
    na_values=["?"],
    low_memory=False
)

print("\n1. Dataset dimensions:")
print(df.shape)

print("\n2. First five records:")
print(df.head())

print("\n3. Columns:")
print(df.columns.tolist())

print("\n4. Missing values:")
print(df.isnull().sum())

print("\n5. Statistical summary:")
print(df.describe())

print("\n6. Memory usage:")
print(f"{df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

print("\nExploration completed!")
