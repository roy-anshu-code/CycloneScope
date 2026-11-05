
import pandas as pd

file_path = "data/raw/ibtracs/ibtracs.NI.list.v04r01.csv"

wind_columns = ["WMO_WIND", "NEWDELHI_WIND", "USA_WIND"]

# Read dataset
df = pd.read_csv(file_path, skiprows=[1], low_memory=False)

# Convert wind columns to numeric
for column in wind_columns:
    df[column] = pd.to_numeric(df[column], errors="coerce")

df["SEASON"] = pd.to_numeric(df["SEASON"], errors="coerce")

df["ISO_TIME"] = pd.to_datetime(
    df["ISO_TIME"],
    errors="coerce",
    utc=True
)

# Keep historical observations from 1980 to 2025
df = df[
    (df["SEASON"] >= 1980)
    & (df["SEASON"] <= 2025)
].copy()

df = df.sort_values(["SID", "ISO_TIME"])

# Create future timestamp
df["future_time"] = (
    df["ISO_TIME"] + pd.Timedelta(hours=24)
)

# Prepare future observations
future = df[["SID", "ISO_TIME"] + wind_columns].copy()

future = future.rename(
    columns={
        "ISO_TIME": "future_time",
        "WMO_WIND": "future_WMO_WIND",
        "NEWDELHI_WIND": "future_NEWDELHI_WIND",
        "USA_WIND": "future_USA_WIND"
    }
)

# Match observations exactly 24 hours apart
pairs = df[
    ["SID", "SEASON", "ISO_TIME", "future_time"] + wind_columns
].merge(
    future,
    on=["SID", "future_time"],
    how="inner"
)

print("\n========== COMMON OBSERVATION ANALYSIS ==========")

print("Total exact 24-hour pairs:", len(pairs))

# Keep only pairs where all three columns have both measurements
required_columns = []

for column in wind_columns:
    required_columns.extend([
        column,
        "future_" + column
    ])

common = pairs.dropna(subset=required_columns).copy()

print("Pairs with all three wind measurements:", len(common))

# Calculate wind changes and RI labels
for column in wind_columns:

    future_column = "future_" + column

    common[column + "_change"] = (
        common[future_column] - common[column]
    )

    common[column + "_RI"] = (
        common[column + "_change"] >= 30
    )

print("\n========== RI EVENTS ON COMMON PAIRS ==========")

for column in wind_columns:

    label = column + "_RI"

    events = common[label].sum()

    print(f"{column}: {events} RI events")

print("\n========== PAIRWISE AGREEMENT ==========")

comparisons = [
    ("WMO_WIND", "NEWDELHI_WIND"),
    ("WMO_WIND", "USA_WIND"),
    ("NEWDELHI_WIND", "USA_WIND")
]

for first, second in comparisons:

    first_label = first + "_RI"
    second_label = second + "_RI"

    agreement = (
        common[first_label] == common[second_label]
    ).sum()

    disagreement = len(common) - agreement

    percentage = agreement / len(common) * 100

    print(f"\n{first} vs {second}")

    print("Agreement:", agreement)
    print("Disagreement:", disagreement)
    print(f"Agreement percentage: {percentage:.2f}%")

    print("\nConfusion table:")
    print(
        pd.crosstab(
            common[first_label],
            common[second_label],
            rownames=[first + " RI"],
            colnames=[second + " RI"]
        )
    )

print("\n========== ANALYSIS COMPLETED ==========")
