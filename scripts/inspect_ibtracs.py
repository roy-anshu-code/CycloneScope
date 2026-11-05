
import pandas as pd

# Dataset path
file_path = "data/raw/ibtracs/ibtracs.NI.list.v04r01.csv"

# Read dataset (skip second row containing units)
df = pd.read_csv(file_path, skiprows=[1], low_memory=False)

print("\n========== BASIC INFORMATION ==========")

print("Total observations:", len(df))
print("Total columns:", len(df.columns))

print("\nFirst 5 observations:")
print(df.head())

print("\n========== STORM INFORMATION ==========")

print("Unique storms:", df["SID"].nunique())

print("\nObservations and unique storms by season:")

season_summary = df.groupby("SEASON").agg(
    observations=("SID", "size"),
    unique_storms=("SID", "nunique")
)

print(season_summary)

print("\n========== DATA TYPE AND MISSING VALUE CHECK ==========")

wind_columns = ["WMO_WIND", "NEWDELHI_WIND", "USA_WIND"]

# Convert wind columns to numeric
for column in wind_columns:
    df[column] = pd.to_numeric(df[column], errors="coerce")

# Convert coordinates to numeric
for column in ["LAT", "LON"]:
    df[column] = pd.to_numeric(df[column], errors="coerce")

for column in wind_columns + ["ISO_TIME", "LAT", "LON"]:
    missing = df[column].isna().sum()
    percentage = (missing / len(df)) * 100

    print(
        f"{column}: {missing} missing "
        f"({percentage:.2f}%)"
    )

print("\n========== WMO AGENCY ==========")

print(df["WMO_AGENCY"].value_counts(dropna=False))

print("\n========== OBSERVATION INTERVALS ==========")

df["ISO_TIME"] = pd.to_datetime(
    df["ISO_TIME"],
    errors="coerce",
    utc=True
)

df = df.sort_values(["SID", "ISO_TIME"])

df["time_difference"] = (
    df.groupby("SID")["ISO_TIME"]
    .diff()
    .dt.total_seconds() / 3600
)

intervals = df["time_difference"].dropna()

print("3-hour intervals:", (intervals == 3).sum())
print("6-hour intervals:", (intervals == 6).sum())
print(
    "Other intervals:",
    (~intervals.isin([3, 6])).sum()
)

print("\nOther interval details:")

other_intervals = intervals[
    ~intervals.isin([3, 6])
]

print(other_intervals.value_counts().head(15))

print("\n========== WIND STATISTICS ==========")

print(df[wind_columns].describe())

print("\n========== WIND VALUE SAMPLES ==========")

for column in wind_columns:
    print(f"\n{column}:")
    print(df[column].dropna().head(10).tolist())

print("\n========== INSPECTION COMPLETED ==========")
