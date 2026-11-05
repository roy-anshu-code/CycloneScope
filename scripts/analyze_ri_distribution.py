import os

import matplotlib.pyplot as plt
import pandas as pd


file_path = "data/raw/ibtracs/ibtracs.NI.list.v04r01.csv"
year_figure_path = "outputs/figures/ri_events_by_year.png"
month_figure_path = "outputs/figures/ri_events_by_month.png"
geography_figure_path = "outputs/figures/ri_geographical_distribution.png"
event_table_path = "outputs/tables/ri_events_newdelhi.csv"

wind_column = "NEWDELHI_WIND"

# Load the original IBTrACS CSV while skipping the units row.
df = pd.read_csv(file_path, skiprows=[1], low_memory=False)

# Convert required numeric and datetime columns.
df["SEASON"] = pd.to_numeric(df["SEASON"], errors="coerce")
df[wind_column] = pd.to_numeric(df[wind_column], errors="coerce")
df["LAT"] = pd.to_numeric(df["LAT"], errors="coerce")
df["LON"] = pd.to_numeric(df["LON"], errors="coerce")
df["ISO_TIME"] = pd.to_datetime(
    df["ISO_TIME"],
    errors="coerce",
    utc=True,
)

# Restrict observations to the historical period.
df = df[
    (df["SEASON"] >= 1980)
    & (df["SEASON"] <= 2025)
].copy()

# Sort by storm and timestamp, then match each observation with the same SID
# exactly 24 hours later.
df = df.sort_values(["SID", "ISO_TIME"])
df["future_time"] = df["ISO_TIME"] + pd.Timedelta(hours=24)

current_columns = [
    "SID",
    "SEASON",
    "NUMBER",
    "BASIN",
    "SUBBASIN",
    "NAME",
    "ISO_TIME",
    "LAT",
    "LON",
    "future_time",
    wind_column,
]
current = df[current_columns].copy()

future = df[["SID", "ISO_TIME", wind_column]].copy()
future = future.rename(
    columns={
        "ISO_TIME": "future_time",
        wind_column: "future_NEWDELHI_WIND",
    }
)

pairs = current.merge(
    future,
    on=["SID", "future_time"],
    how="inner",
)

# Exclude pairs where current or future NEWDELHI wind is missing.
valid_pairs = pairs[
    pairs[wind_column].notna()
    & pairs["future_NEWDELHI_WIND"].notna()
].copy()

valid_pairs["wind_change"] = (
    valid_pairs["future_NEWDELHI_WIND"] - valid_pairs[wind_column]
)
valid_pairs["RI"] = valid_pairs["wind_change"] >= 30

ri_events = valid_pairs[valid_pairs["RI"]].copy()
ri_events["year"] = ri_events["ISO_TIME"].dt.year
ri_events["month"] = ri_events["ISO_TIME"].dt.month
ri_events["month_name"] = ri_events["ISO_TIME"].dt.strftime("%B")

ri_events = ri_events.rename(
    columns={
        "ISO_TIME": "event_time",
        wind_column: "current_newdelhi_wind",
        "future_NEWDELHI_WIND": "future_newdelhi_wind",
        "wind_change": "wind_increase_24h",
        "LAT": "latitude",
        "LON": "longitude",
    }
)

print("\n========== NEWDELHI RI EVENT DISTRIBUTION ==========")
print("Filtered observations:", len(df))
print("Exact 24-hour observation pairs:", len(pairs))
print("Valid pairs with NEWDELHI wind available:", len(valid_pairs))
print("Overall valid-pair coverage percentage:",
      round(len(valid_pairs) / len(pairs) * 100, 2) if len(pairs) > 0 else 0.0)
print("Total RI events:", len(ri_events))
print("Unique storms with RI events:", ri_events["SID"].nunique())

if len(ri_events) > 0:
    print("Earliest RI event date:", ri_events["event_time"].min())
    print("Latest RI event date:", ri_events["event_time"].max())

    print(
        "Minimum latitude:",
        ri_events["latitude"].min(skipna=True),
    )
    print(
        "Maximum latitude:",
        ri_events["latitude"].max(skipna=True),
    )
    print(
        "Minimum longitude:",
        ri_events["longitude"].min(skipna=True),
    )
    print(
        "Maximum longitude:",
        ri_events["longitude"].max(skipna=True),
    )

    yearly_counts = (
        ri_events["year"]
        .value_counts()
        .sort_index()
        .rename_axis("Year")
        .reset_index(name="RI Events")
    )
    print("\nRI events by year:")
    print(yearly_counts.to_string(index=False))

    month_order = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ]
    monthly_counts = (
        ri_events["month_name"]
        .value_counts()
        .reindex(month_order, fill_value=0)
        .rename_axis("Month")
        .reset_index(name="RI Events")
    )
    print("\nRI events by month:")
    print(monthly_counts.to_string(index=False))

    basin_counts = (
        ri_events.groupby(["BASIN", "SUBBASIN"], dropna=False)
        .size()
        .rename("RI Events")
        .reset_index()
        .sort_values(["BASIN", "SUBBASIN"], na_position="last")
    )
    print("\nRI events by basin and subbasin:")
    print(basin_counts.to_string(index=False))

    subbasin_counts = (
        ri_events["SUBBASIN"]
        .value_counts(dropna=False)
        .rename_axis("SUBBASIN")
        .reset_index(name="RI Events")
        .sort_values(["RI Events", "SUBBASIN"], ascending=[False, True])
    )
    print("\nRI event counts by subbasin:")
    print(subbasin_counts.to_string(index=False))
else:
    yearly_counts = pd.DataFrame({"Year": [], "RI Events": []})
    monthly_counts = pd.DataFrame({"Month": [], "RI Events": []})
    basin_counts = pd.DataFrame()
    subbasin_counts = pd.DataFrame()
    print("Earliest RI event date: N/A")
    print("Latest RI event date: N/A")
    print("Latitude and longitude minimum/maximum: N/A")
    print("\nRI events by year: No events")
    print("\nRI events by month: No events")
    print("\nRI events by basin and subbasin: No events")
    print("\nRI event counts by subbasin: No events")

# Analyze geographical coverage of valid RI observation pairs.
valid_coordinates = valid_pairs[
    valid_pairs["LAT"].notna()
    & valid_pairs["LON"].notna()
]
print("\n========== OVERALL GEOGRAPHIC COVERAGE ==========")
print("Valid RI-capable pairs:", len(valid_pairs))
print("Valid pairs with coordinates:", len(valid_coordinates))
print(
    "Valid pairs missing coordinates:",
    len(valid_pairs) - len(valid_coordinates),
)
if len(valid_coordinates) > 0:
    print("Valid-pair minimum latitude:", valid_coordinates["LAT"].min())
    print("Valid-pair maximum latitude:", valid_coordinates["LAT"].max())
    print("Valid-pair minimum longitude:", valid_coordinates["LON"].min())
    print("Valid-pair maximum longitude:", valid_coordinates["LON"].max())

os.makedirs("outputs/figures", exist_ok=True)
os.makedirs("outputs/tables", exist_ok=True)

# RI events per year.
if len(yearly_counts) > 0:
    plt.figure(figsize=(12, 6))
    plt.bar(yearly_counts["Year"], yearly_counts["RI Events"], color="steelblue")
    plt.xlabel("Year")
    plt.ylabel("Number of RI Events")
    plt.title("NEWDELHI Wind RI Events per Year (1980-2025)")
    plt.xticks(rotation=45)
    plt.tight_layout()
else:
    plt.figure(figsize=(8, 4))
    plt.text(0.5, 0.5, "No RI events found", ha="center", va="center")
    plt.title("NEWDELHI Wind RI Events per Year (1980-2025)")
plt.savefig(year_figure_path, dpi=150, bbox_inches="tight")
plt.close()

# RI events per month.
if len(monthly_counts) > 0:
    plt.figure(figsize=(12, 6))
    plt.bar(
        monthly_counts["Month"],
        monthly_counts["RI Events"],
        color="darkorange",
    )
    plt.xlabel("Month")
    plt.ylabel("Number of RI Events")
    plt.title("NEWDELHI Wind RI Events per Month")
    plt.xticks(rotation=45)
    plt.tight_layout()
else:
    plt.figure(figsize=(8, 4))
    plt.text(0.5, 0.5, "No RI events found", ha="center", va="center")
    plt.title("NEWDELHI Wind RI Events per Month")
plt.savefig(month_figure_path, dpi=150, bbox_inches="tight")
plt.close()

# Geographic scatter plot of RI event locations.
coordinate_events = (
    ri_events[
        ri_events["latitude"].notna()
        & ri_events["longitude"].notna()
    ]
    if len(ri_events) > 0
    else ri_events
)

plt.figure(figsize=(10, 7))
if len(coordinate_events) > 0:
    plt.scatter(
        coordinate_events["longitude"],
        coordinate_events["latitude"],
        s=20,
        alpha=0.65,
        color="crimson",
    )
else:
    plt.text(
        0.5,
        0.5,
        "No RI events with coordinates",
        ha="center",
        va="center",
        transform=plt.gca().transAxes,
    )
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.title("Geographic Distribution of NEWDELHI Wind RI Events")
plt.grid(alpha=0.25)
plt.tight_layout()
plt.savefig(geography_figure_path, dpi=150, bbox_inches="tight")
plt.close()

table_columns = [
    "SID",
    "SEASON",
    "NUMBER",
    "BASIN",
    "SUBBASIN",
    "NAME",
    "event_time",
    "latitude",
    "longitude",
    "current_newdelhi_wind",
    "future_newdelhi_wind",
    "wind_increase_24h",
]
ri_events[table_columns].to_csv(event_table_path, index=False)

print("\nSaved RI events table:", event_table_path)
print("Saved year figure:", year_figure_path)
print("Saved month figure:", month_figure_path)
print("Saved geographic figure:", geography_figure_path)
print("\n========== ANALYSIS COMPLETED ==========")
