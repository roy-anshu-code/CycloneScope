import pandas as pd


file_path = "data/raw/ibtracs/ibtracs.NI.list.v04r01.csv"
wind_columns = ["WMO_WIND", "NEWDELHI_WIND", "USA_WIND"]

# Load the original dataset and skip the units row.
df = pd.read_csv(file_path, skiprows=[1], low_memory=False)

# Convert required columns to numeric values.
for column in wind_columns:
    df[column] = pd.to_numeric(df[column], errors="coerce")

df["SEASON"] = pd.to_numeric(df["SEASON"], errors="coerce")

# Restrict the analysis to seasons 1980 through 2025.
df = df[
    (df["SEASON"] >= 1980)
    & (df["SEASON"] <= 2025)
].copy()

# Trim agency names and treat blank strings as missing.
df["WMO_AGENCY"] = df["WMO_AGENCY"].astype("string").str.strip()
df["WMO_AGENCY"] = df["WMO_AGENCY"].replace("", pd.NA)

total_observations = len(df)

print("\n========== WMO AGENCY OBSERVATION COUNTS ==========")
agency_counts = (
    df["WMO_AGENCY"]
    .value_counts(dropna=True)
    .rename_axis("WMO_AGENCY")
    .reset_index(name="Observation Count")
)
agency_counts["Percentage of Total Observations"] = (
    agency_counts["Observation Count"] / total_observations * 100
)
print(agency_counts.to_string(index=False))

missing_agencies = df["WMO_AGENCY"].isna().sum()
print("\n========== MISSING OR BLANK AGENCY VALUES ==========")
print("Missing/blank agency observations:", missing_agencies)
print(
    "Percentage of total observations:",
    round(missing_agencies / total_observations * 100, 2),
    "%",
)

print("\n========== WIND MEASUREMENTS BY WMO AGENCY ==========")
agency_data = df[df["WMO_AGENCY"].notna()].copy()
availability = []
statistics = []

for agency, agency_rows in agency_data.groupby("WMO_AGENCY", sort=True):
    availability_row = {
        "WMO_AGENCY": agency,
        "Total Observations": len(agency_rows),
    }
    statistics_row = {"WMO_AGENCY": agency}

    for column in wind_columns:
        available = agency_rows[column].notna().sum()
        availability_row[column + " Available"] = available

        statistics_row[column + " Mean"] = (
            round(agency_rows[column].mean(), 2)
            if available > 0
            else float("nan")
        )
        statistics_row[column + " Maximum"] = (
            agency_rows[column].max() if available > 0 else float("nan")
        )

    availability.append(availability_row)
    statistics.append(statistics_row)

availability_table = pd.DataFrame(availability)
statistics_table = pd.DataFrame(statistics)

print("\nAvailable wind measurements:")
print(availability_table.to_string(index=False))

print("\nMean and maximum wind speeds (knots):")
print(statistics_table.to_string(index=False, na_rep="N/A"))

print("\n========== WMO_WIND AND NEWDELHI_WIND POPULATION ==========")

wmo_available = df["WMO_WIND"].notna()
newdelhi_available = df["NEWDELHI_WIND"].notna()

population_counts = pd.DataFrame({
    "Category": [
        "Both populated",
        "WMO_WIND only",
        "NEWDELHI_WIND only",
        "Both missing",
    ],
    "Observation Count": [
        (wmo_available & newdelhi_available).sum(),
        (wmo_available & ~newdelhi_available).sum(),
        (~wmo_available & newdelhi_available).sum(),
        (~wmo_available & ~newdelhi_available).sum(),
    ],
})
population_counts["Percentage of Total Observations"] = (
    population_counts["Observation Count"] / total_observations * 100
)
print("\nOverall overlap:")
print(population_counts.to_string(index=False))

overlap_rows = []
for agency, agency_rows in agency_data.groupby("WMO_AGENCY", sort=True):
    wmo = agency_rows["WMO_WIND"].notna()
    newdelhi = agency_rows["NEWDELHI_WIND"].notna()

    overlap_rows.append({
        "WMO_AGENCY": agency,
        "Total Observations": len(agency_rows),
        "Both Populated": (wmo & newdelhi).sum(),
        "WMO Only": (wmo & ~newdelhi).sum(),
        "NEWDELHI Only": (~wmo & newdelhi).sum(),
        "Both Missing": (~wmo & ~newdelhi).sum(),
    })

missing_overlap = {
    "WMO_AGENCY": "(Missing/Blank)",
    "Total Observations": missing_agencies,
    "Both Populated": (
        wmo_available
        & newdelhi_available
        & df["WMO_AGENCY"].isna()
    ).sum(),
    "WMO Only": (
        wmo_available
        & ~newdelhi_available
        & df["WMO_AGENCY"].isna()
    ).sum(),
    "NEWDELHI Only": (
        ~wmo_available
        & newdelhi_available
        & df["WMO_AGENCY"].isna()
    ).sum(),
    "Both Missing": (
        ~wmo_available
        & ~newdelhi_available
        & df["WMO_AGENCY"].isna()
    ).sum(),
}
overlap_rows.append(missing_overlap)

overlap_table = pd.DataFrame(overlap_rows)
print("\nWMO/NEWDELHI population by agency:")
print(overlap_table.to_string(index=False))

print("\n========== SHORT SUMMARY ==========")
print(
    "Total filtered observations:",
    total_observations,
)
print(
    "Wind columns available overall:",
    {
        column: int(df[column].notna().sum())
        for column in wind_columns
    },
)
print(
    "Overall WMO/NEWDELHI both-populated observations:",
    int((wmo_available & newdelhi_available).sum()),
)
print(
    "Overall WMO-only observations:",
    int((wmo_available & ~newdelhi_available).sum()),
)
print(
    "Overall NEWDELHI-only observations:",
    int((~wmo_available & newdelhi_available).sum()),
)
print(
    "Overall both-missing observations:",
    int((~wmo_available & ~newdelhi_available).sum()),
)
print("\n========== ANALYSIS COMPLETED ==========")
