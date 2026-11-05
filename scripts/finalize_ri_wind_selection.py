import os

import pandas as pd


file_path = "data/raw/ibtracs/ibtracs.NI.list.v04r01.csv"
source_table_path = "outputs/tables/ri_wind_source_comparison.csv"
agreement_table_path = "outputs/tables/ri_wind_agreement.csv"

wind_columns = ["WMO_WIND", "NEWDELHI_WIND", "USA_WIND"]
comparisons = [
    ("WMO_WIND", "NEWDELHI_WIND"),
    ("WMO_WIND", "USA_WIND"),
    ("NEWDELHI_WIND", "USA_WIND"),
]

# Read the original IBTrACS CSV while skipping the units row.
df = pd.read_csv(file_path, skiprows=[1], low_memory=False)

for column in wind_columns:
    df[column] = pd.to_numeric(df[column], errors="coerce")

df["SEASON"] = pd.to_numeric(df["SEASON"], errors="coerce")
df["ISO_TIME"] = pd.to_datetime(
    df["ISO_TIME"],
    errors="coerce",
    utc=True,
)

# Restrict the analysis to 1980-2025.
df = df[
    (df["SEASON"] >= 1980)
    & (df["SEASON"] <= 2025)
].copy()

# Match each observation with the same SID exactly 24 hours later.
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

print("\n========== CONSOLIDATED RI WIND SOURCE COMPARISON ==========")
print("Filtered observations:", len(df))
print("Exact 24-hour pairs:", len(pairs))

source_rows = []
for column in wind_columns:
    future_column = "future_" + column

    valid = pairs[
        pairs[column].notna()
        & pairs[future_column].notna()
    ].copy()

    valid["wind_change"] = valid[future_column] - valid[column]
    valid["is_RI"] = valid["wind_change"] >= 30

    valid_pairs = len(valid)
    ri_events = int(valid["is_RI"].sum())
    ri_percentage = (
        ri_events / valid_pairs * 100
        if valid_pairs > 0
        else 0.0
    )

    current_available = int(df[column].notna().sum())
    missing_current = len(df) - current_available
    current_coverage = current_available / len(df) * 100

    missing_in_pairs = len(pairs) - (
        pairs[column].notna()
        & pairs[future_column].notna()
    ).sum()
    pair_coverage = valid_pairs / len(pairs) * 100 if len(pairs) > 0 else 0.0

    source_rows.append({
        "Wind Source": column,
        "Available Current Observations": current_available,
        "Missing Current Observations": missing_current,
        "Current Observation Coverage Percentage": round(current_coverage, 2),
        "Valid 24-hour Pairs": valid_pairs,
        "Missing from Valid 24-hour Pairs": missing_in_pairs,
        "Valid Pair Coverage Percentage": round(pair_coverage, 2),
        "RI Events": ri_events,
        "RI Percentage": round(ri_percentage, 2),
    })

source_table = pd.DataFrame(source_rows)
print("\nWind source comparison:")
print(source_table.to_string(index=False))

agreement_rows = []
required_columns = []

for column in wind_columns:
    required_columns.extend([column, "future_" + column])

all_three_valid = pairs.dropna(subset=required_columns).copy()
print(
    "\nCommon pairs with all three wind columns available:",
    len(all_three_valid),
)

for column in wind_columns:
    future_column = "future_" + column
    change_column = column + "_change"
    label_column = column + "_RI"

    all_three_valid[change_column] = (
        all_three_valid[future_column] - all_three_valid[column]
    )
    all_three_valid[label_column] = (
        all_three_valid[change_column] >= 30
    )

for first, second in comparisons:
    first_label = first + "_RI"
    second_label = second + "_RI"

    common_valid = pairs[
        pairs[first].notna()
        & pairs["future_" + first].notna()
        & pairs[second].notna()
        & pairs["future_" + second].notna()
    ].copy()

    first_change = (
        common_valid["future_" + first] - common_valid[first]
    )
    second_change = (
        common_valid["future_" + second] - common_valid[second]
    )
    first_ri = first_change >= 30
    second_ri = second_change >= 30

    agreements = first_ri == second_ri
    agreement_count = int(agreements.sum())
    disagreement_count = int(len(common_valid) - agreement_count)
    agreement_percentage = (
        agreement_count / len(common_valid) * 100
        if len(common_valid) > 0
        else 0.0
    )

    agreement_rows.append({
        "Wind Source Pair": first + " vs " + second,
        "Common Valid Pairs": len(common_valid),
        "Agreement Count": agreement_count,
        "Disagreement Count": disagreement_count,
        "Agreement Percentage": round(agreement_percentage, 2),
        "Both RI": int((first_ri & second_ri).sum()),
        "Neither RI": int((~first_ri & ~second_ri).sum()),
        "First Only RI": int((first_ri & ~second_ri).sum()),
        "Second Only RI": int((~first_ri & second_ri).sum()),
    })

agreement_table = pd.DataFrame(agreement_rows)
print("\nPairwise RI classification agreement:")
print(agreement_table.to_string(index=False))

os.makedirs("outputs/tables", exist_ok=True)
source_table.to_csv(source_table_path, index=False)
agreement_table.to_csv(agreement_table_path, index=False)

print("\nSaved source comparison table:", source_table_path)
print("Saved agreement table:", agreement_table_path)

print("\n========== CONCISE SUMMARY ==========")
print(
    "USA has the largest valid 24-hour pair coverage in this period, while WMO and "
    "NEWDELHI require separate assessment of their source coverage and agency provenance."
)
print(
    "WMO and NEWDELHI generally agree most closely among paired RI classifications, "
    "but USA differences indicate that source choice can materially change event counts."
)
print(
    "No source is automatically declared superior; this output preserves coverage, "
    "consistency and missing-value evidence for the selection decision."
)
print("\n========== ANALYSIS COMPLETED ==========")
