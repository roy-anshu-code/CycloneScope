import pandas as pd


file_path = "data/raw/ibtracs/ibtracs.NI.list.v04r01.csv"

wind_columns = ["WMO_WIND", "NEWDELHI_WIND", "USA_WIND"]

comparisons = [
    ("WMO_WIND", "NEWDELHI_WIND"),
    ("WMO_WIND", "USA_WIND"),
    ("NEWDELHI_WIND", "USA_WIND"),
]

# Read the original IBTrACS CSV while skipping the units row.
df = pd.read_csv(file_path, skiprows=[1], low_memory=False)

# Convert the required wind and season columns to numeric values.
for column in wind_columns:
    df[column] = pd.to_numeric(df[column], errors="coerce")

df["SEASON"] = pd.to_numeric(df["SEASON"], errors="coerce")

# Parse timestamps and restrict the analysis to 1980-2025.
df["ISO_TIME"] = pd.to_datetime(
    df["ISO_TIME"],
    errors="coerce",
    utc=True,
)

df = df[
    (df["SEASON"] >= 1980)
    & (df["SEASON"] <= 2025)
].copy()


print("\n========== COMMON OBSERVATION WIND VALUES ==========")

common_observations = df.dropna(subset=wind_columns).copy()

print(
    "Observations with all three wind values available:",
    len(common_observations),
)

for first, second in comparisons:
    differences = (
        common_observations[first] - common_observations[second]
    ).abs()

    identical_count = (
        common_observations[first]
        == common_observations[second]
    ).sum()

    different_count = len(common_observations) - identical_count

    print(f"\n{first} vs {second}")
    print("Identical wind values:", identical_count)
    print("Different wind values:", different_count)

    if len(common_observations) > 0:
        print(
            "Mean absolute difference:",
            round(differences.mean(), 2),
            "knots",
        )
        print(
            "Maximum absolute difference:",
            differences.max(),
            "knots",
        )
    else:
        print("Mean absolute difference: N/A")
        print("Maximum absolute difference: N/A")


# Match observations from the same SID exactly 24 hours apart.
df = df.sort_values(["SID", "ISO_TIME"])

current = df[["SID", "ISO_TIME"] + wind_columns].copy()
current["future_time"] = current["ISO_TIME"] + pd.Timedelta(hours=24)

future = df[["SID", "ISO_TIME"] + wind_columns].copy()
future = future.rename(
    columns={
        "ISO_TIME": "future_time",
        "WMO_WIND": "future_WMO_WIND",
        "NEWDELHI_WIND": "future_NEWDELHI_WIND",
        "USA_WIND": "future_USA_WIND",
    }
)

pairs = current.merge(
    future,
    on=["SID", "future_time"],
    how="inner",
)

required_pair_columns = []
for column in wind_columns:
    required_pair_columns.extend([column, "future_" + column])

common_pairs = pairs.dropna(subset=required_pair_columns).copy()

print("\n========== EXACT 24-HOUR WIND CHANGES ==========")

print("Total exact 24-hour pairs:", len(pairs))
print(
    "Pairs with all three wind columns available at both times:",
    len(common_pairs),
)

for column in wind_columns:
    common_pairs[column + "_change"] = (
        common_pairs["future_" + column] - common_pairs[column]
    )

for first, second in comparisons:
    first_change = first + "_change"
    second_change = second + "_change"

    change_differences = (
        common_pairs[first_change] - common_pairs[second_change]
    ).abs()

    identical_changes = (
        common_pairs[first_change] == common_pairs[second_change]
    ).sum()

    different_changes = len(common_pairs) - identical_changes

    print(f"\n{first} vs {second}")
    print("Identical changes:", identical_changes)
    print("Different changes:", different_changes)

    if len(common_pairs) > 0:
        print(
            "Mean absolute difference:",
            round(change_differences.mean(), 2),
            "knots",
        )
    else:
        print("Mean absolute difference: N/A")

print("\n========== ANALYSIS COMPLETED ==========")
