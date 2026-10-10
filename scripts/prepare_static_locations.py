import os
import pandas as pd


# ============================================================
# PATHS
# ============================================================

INPUT_PATH = "data/master_data.csv"
OUTPUT_PATH = "data/static_locations.csv"


# ============================================================
# STATIC SPATIAL FEATURES
# ============================================================
#
# These values do not change from day to day for a location.
# ============================================================

STATIC_FEATURES = [
    "Elevation_m",
    "Slope_deg",
    "Flow_Accumulation_km2",
    "Builtup_Percent",
    "Vegetation_Percent",
    "Road_Density_km_per_km2",
    "Distance_to_River_m",
    "Distance_to_Drain_m",
    "Drainage_Density_km_per_km2",
]


# ============================================================
# LOAD DATA
# ============================================================

print("Loading master dataset...")

df = pd.read_csv(
    INPUT_PATH
)

print(
    f"Rows loaded: {len(df):,}"
)


# ============================================================
# CHECK REQUIRED COLUMNS
# ============================================================

required_columns = [
    "Ward_Name",
    "Point_ID",
    "Latitude",
    "Longitude",
] + STATIC_FEATURES


missing = [
    col
    for col in required_columns
    if col not in df.columns
]

if missing:

    raise ValueError(
        "Missing required columns:\n"
        + "\n".join(
            f"- {col}"
            for col in missing
        )
    )


# ============================================================
# CREATE LOCATION ID
# ============================================================
#
# P01 is repeated across wards.
# Ward + Point identifies a physical sampling location.
# ============================================================

df["location_id"] = (
    df["Ward_Name"].astype(str)
    + "__"
    + df["Point_ID"].astype(str)
)


# ============================================================
# SELECT ONE ROW PER LOCATION
# ============================================================
#
# Static fields are expected to be identical across all
# dates for the same physical location.
# ============================================================

location_columns = [
    "location_id",
    "Ward_Name",
    "Point_ID",
    "Latitude",
    "Longitude",
] + STATIC_FEATURES


static_df = (
    df[location_columns]
    .drop_duplicates(
        subset=["location_id"]
    )
    .sort_values(
        [
            "Ward_Name",
            "Point_ID"
        ]
    )
    .reset_index(
        drop=True
    )
)


# ============================================================
# VERIFY LOCATION COUNT
# ============================================================

print(
    f"Unique physical locations: "
    f"{len(static_df)}"
)


if len(static_df) != 482:

    print(
        "WARNING: Expected 482 "
        "physical sampling locations."
    )


# ============================================================
# VERIFY STATIC FEATURES ARE ACTUALLY STATIC
# ============================================================

grouped = df.groupby(
    "location_id"
)

print(
    "\nChecking static feature consistency..."
)


for feature in [
    "Latitude",
    "Longitude"
] + STATIC_FEATURES:

    varying_locations = (
        grouped[feature]
        .nunique()
        .gt(1)
        .sum()
    )

    if varying_locations > 0:

        raise ValueError(
            f"Feature '{feature}' "
            f"changes across dates for "
            f"{varying_locations} locations."
        )

    print(
        f"  {feature}: OK"
    )


# ============================================================
# PHYSICAL PERCENTAGE LIMITS
# ============================================================

static_df["Builtup_Percent"] = (
    static_df["Builtup_Percent"]
    .clip(0, 100)
)

static_df["Vegetation_Percent"] = (
    static_df["Vegetation_Percent"]
    .clip(0, 100)
)


# ============================================================
# SAVE
# ============================================================

os.makedirs(
    os.path.dirname(OUTPUT_PATH),
    exist_ok=True
)

static_df.to_csv(
    OUTPUT_PATH,
    index=False
)


# ============================================================
# SHOW SAMPLE
# ============================================================

print(
    "\nFirst 10 locations:"
)

print(
    static_df.head(10).to_string(
        index=False
    )
)


print(
    "\n" + "=" * 70
)

print(
    "STEP 7B COMPLETE"
)

print(
    "=" * 70
)

print(
    f"Static location file:\n"
    f"{OUTPUT_PATH}"
)

print(
    f"Locations stored: "
    f"{len(static_df)}"
)