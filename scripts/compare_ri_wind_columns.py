
import pandas as pd

# Dataset path
file_path = "data/raw/ibtracs/ibtracs.NI.list.v04r01.csv"

# Read dataset
df = pd.read_csv(file_path, skiprows=[1], low_memory=False)

wind_columns = ["WMO_WIND", "NEWDELHI_WIND", "USA_WIND"]

# Convert wind columns to numeric
for column in wind_columns:
    df[column] = pd.to_numeric(df[column], errors="coerce")

# Convert dates
df["ISO_TIME"] = pd.to_datetime(
    df["ISO_TIME"],
    errors="coerce",
    utc=True
)

df["SEASON"] = pd.to_numeric(df["SEASON"], errors="coerce")

# Sort observations
df = df.sort_values(["SID", "ISO_TIME"])

# Create future timestamp
df["future_time"] = (
    df["ISO_TIME"] + pd.Timedelta(hours=24)
)

# Prepare future observations
future = df[
    ["SID", "ISO_TIME"] + wind_columns
].copy()

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

print("\n========== RI DETECTION COMPARISON ==========")

print("Total exact 24-hour pairs:", len(pairs))

# Analyse different historical periods
periods = {
    "All years": 0,
    "Since 1980": 1980,
    "Since 1990": 1990,
    "Since 2000": 2000,
    "Since 2010": 2010
}

for period_name, start_year in periods.items():

    subset = pairs[pairs["SEASON"] >= start_year]

    print(f"\n========== {period_name} ==========")

    print("Total observation pairs:", len(subset))

    for column in wind_columns:

        future_column = "future_" + column

        # Keep only pairs with both wind measurements
        valid = subset[
            subset[column].notna()
            & subset[future_column].notna()
        ].copy()

        # Calculate 24-hour wind change
        valid["wind_change"] = (
            valid[future_column] - valid[column]
        )

        # RI definition: increase of at least 30 knots
        ri_events = valid[
            valid["wind_change"] >= 30
        ]

        print(f"\n{column}")
        print("Valid wind pairs:", len(valid))
        print("RI events:", len(ri_events))

        if len(valid) > 0:
            percentage = len(ri_events) / len(valid) * 100

            print(f"RI percentage: {percentage:.2f}%")

            print(
                "Average 24-hour wind change:",
                round(valid["wind_change"].mean(), 2),
                "knots"
            )

            print(
                "Maximum 24-hour wind increase:",
                valid["wind_change"].max(),
                "knots"
            )

print("\n========== COMPARISON COMPLETED ==========")
