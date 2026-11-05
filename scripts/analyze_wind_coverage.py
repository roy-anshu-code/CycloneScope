
import pandas as pd

# Dataset path
file_path = "data/raw/ibtracs/ibtracs.NI.list.v04r01.csv"

# Read dataset
df = pd.read_csv(file_path, skiprows=[1], low_memory=False)

# Convert columns
wind_columns = ["WMO_WIND", "NEWDELHI_WIND", "USA_WIND"]

for column in wind_columns:
    df[column] = pd.to_numeric(df[column], errors="coerce")

df["SEASON"] = pd.to_numeric(df["SEASON"], errors="coerce")

print("\n========== DATASET PERIOD ==========")

print("First season:", df["SEASON"].min())
print("Last season:", df["SEASON"].max())

# Analyse different historical periods
periods = {
    "All years": 0,
    "Since 1980": 1980,
    "Since 1990": 1990,
    "Since 2000": 2000,
    "Since 2010": 2010
}

print("\n========== WIND COVERAGE BY PERIOD ==========")

for period_name, start_year in periods.items():

    subset = df[df["SEASON"] >= start_year]

    print(f"\n{period_name}")
    print("Total observations:", len(subset))

    for column in wind_columns:

        available = subset[column].notna().sum()
        percentage = available / len(subset) * 100

        print(
            f"{column}: {available} observations "
            f"({percentage:.2f}%)"
        )

print("\n========== YEAR-WISE WIND COVERAGE ==========")

yearly = df.groupby("SEASON").agg(
    observations=("SID", "size"),
    unique_storms=("SID", "nunique"),
    WMO_available=("WMO_WIND", "count"),
    NewDelhi_available=("NEWDELHI_WIND", "count"),
    USA_available=("USA_WIND", "count")
)

for column in [
    "WMO_available",
    "NewDelhi_available",
    "USA_available"
]:
    yearly[column + "_percentage"] = (
        yearly[column] / yearly["observations"] * 100
    )

print(yearly.tail(30).to_string())

print("\n========== WIND COLUMN OVERLAP ==========")

for first, second in [
    ("WMO_WIND", "NEWDELHI_WIND"),
    ("WMO_WIND", "USA_WIND"),
    ("NEWDELHI_WIND", "USA_WIND")
]:

    both_available = (
        df[first].notna() & df[second].notna()
    ).sum()

    print(
        f"{first} and {second}: "
        f"{both_available} common observations"
    )

print("\n========== EXACT 24-HOUR WIND PAIRS ==========")

df["ISO_TIME"] = pd.to_datetime(
    df["ISO_TIME"],
    errors="coerce",
    utc=True
)

# Keep only required columns for matching
current = df[["SID", "ISO_TIME"] + wind_columns].copy()

# Identify duplicate storm timestamps
duplicates = current.duplicated(
    subset=["SID", "ISO_TIME"]
).sum()

print("Duplicate storm timestamps:", duplicates)

# Match each observation with the same storm exactly 24 hours later
current["future_time"] = (
    current["ISO_TIME"] + pd.Timedelta(hours=24)
)

future = current[["SID", "ISO_TIME"] + wind_columns].copy()

future = future.rename(
    columns={
        "ISO_TIME": "future_time",
        "WMO_WIND": "future_WMO_WIND",
        "NEWDELHI_WIND": "future_NEWDELHI_WIND",
        "USA_WIND": "future_USA_WIND"
    }
)

pairs = current.merge(
    future,
    on=["SID", "future_time"],
    how="inner"
)

print("Exact 24-hour observation pairs:", len(pairs))

for column in wind_columns:

    future_column = "future_" + column

    valid_pairs = (
        pairs[column].notna()
        & pairs[future_column].notna()
    ).sum()

    print(
        f"{column}: {valid_pairs} pairs "
        "with both wind measurements available"
    )

print("\n========== ANALYSIS COMPLETED ==========")
