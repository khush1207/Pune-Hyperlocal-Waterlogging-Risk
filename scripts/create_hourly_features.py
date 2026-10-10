from pathlib import Path
import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent

PARQUET_ROOT = (
    PROJECT_ROOT
    / "data"
    / "hourly_parquet"
)

FEATURE_ROOT = (
    PROJECT_ROOT
    / "data"
    / "hourly_features"
)

STATIC_FILE = (
    PROJECT_ROOT
    / "data"
    / "static_locations.csv"
)


# ------------------------------------------------------------
# TEST MODE
# ------------------------------------------------------------
# True  -> process only January 2021 first
# False -> process all 2021–2025
# ------------------------------------------------------------

TEST_MODE = False

TEST_YEAR = 2021
TEST_MONTH = 1


START_YEAR = 2021
END_YEAR = 2025


EXPECTED_LOCATION_COUNT = 482


# Largest rolling window = 168 hours
LOOKBACK_HOURS = 168


# ============================================================
# STATIC FEATURES
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
# WEATHER COLUMN NORMALIZATION
# ============================================================

def normalize_weather_columns(df):

    rename_map = {}

    # Older files
    if "location_id" in df.columns:
        rename_map["location_id"] = "Location_ID"

    if "Humidity_Percent" in df.columns:
        rename_map["Humidity_Percent"] = (
            "Relative_Humidity_pct"
        )

    if "Shortwave_Radiation_Wm2" in df.columns:
        rename_map["Shortwave_Radiation_Wm2"] = (
            "Shortwave_Radiation_W_m2"
        )

    df = df.rename(
        columns=rename_map
    )

    required = [
        "Location_ID",
        "Latitude",
        "Longitude",
        "DateTime",
        "Rain_mm",
        "Temperature_C",
        "Relative_Humidity_pct",
        "Wind_Speed_kmh",
        "Shortwave_Radiation_W_m2",
    ]

    missing = [
        col
        for col in required
        if col not in df.columns
    ]

    if missing:
        raise RuntimeError(
            f"Missing weather columns: {missing}"
        )

    return df[required].copy()


# ============================================================
# DATETIME
# ============================================================

def normalize_datetime(series):

    parsed = pd.to_datetime(
        series,
        errors="coerce",
    )

    if isinstance(
        parsed.dtype,
        pd.DatetimeTZDtype,
    ):

        parsed = (
            parsed
            .dt.tz_convert("Asia/Kolkata")
            .dt.tz_localize(None)
        )

    return parsed


# ============================================================
# LOAD STATIC DATA
# ============================================================

def load_static_data():

    static = pd.read_csv(
        STATIC_FILE
    )

    # Normalize location ID
    if "location_id" in static.columns:

        static = static.rename(
            columns={
                "location_id": "Location_ID"
            }
        )

    elif "Location_ID" not in static.columns:

        if (
            "Ward_Name" in static.columns
            and "Point_ID" in static.columns
        ):

            static["Location_ID"] = (
                static["Ward_Name"]
                .astype(str)
                .str.strip()
                + "__"
                + static["Point_ID"]
                .astype(str)
                .str.strip()
            )

        else:

            raise RuntimeError(
                "Could not create Location_ID "
                "from static_locations.csv."
            )

    static["Location_ID"] = (
        static["Location_ID"]
        .astype(str)
        .str.strip()
    )

    # Keep only required static features
    required = [
        "Location_ID",
        *STATIC_FEATURES,
    ]

    missing = [
        col
        for col in required
        if col not in static.columns
    ]

    if missing:

        raise RuntimeError(
            f"Missing static columns: {missing}"
        )

    static = static[required].copy()

    static = static.drop_duplicates(
        subset=["Location_ID"]
    )

    if len(static) != EXPECTED_LOCATION_COUNT:

        raise RuntimeError(
            f"Expected {EXPECTED_LOCATION_COUNT} "
            f"static locations, found "
            f"{len(static)}"
        )

    return static


# ============================================================
# LOAD MONTH
# ============================================================

def load_month(year, month):

    file_path = (
        PARQUET_ROOT
        / str(year)
        / f"{month:02d}.parquet"
    )

    if not file_path.exists():

        raise FileNotFoundError(
            f"Parquet file not found:\n"
            f"{file_path}"
        )

    print(
        f"Reading: {file_path}"
    )

    df = pd.read_parquet(
        file_path
    )

    df = normalize_weather_columns(
        df
    )

    df["DateTime"] = normalize_datetime(
        df["DateTime"]
    )

    numeric_columns = [
        "Latitude",
        "Longitude",
        "Rain_mm",
        "Temperature_C",
        "Relative_Humidity_pct",
        "Wind_Speed_kmh",
        "Shortwave_Radiation_W_m2",
    ]

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    # Rainfall cannot be negative
    df["Rain_mm"] = (
        df["Rain_mm"]
        .fillna(0)
        .clip(lower=0)
    )

    df = df.sort_values(
        [
            "Location_ID",
            "DateTime",
        ]
    ).reset_index(
        drop=True
    )

    return df


# ============================================================
# ROLLING FEATURES
# ============================================================

def create_rolling_features(df):

    print(
        "Creating rainfall persistence features..."
    )

    grouped = df.groupby(
        "Location_ID",
        sort=False,
    )

    # --------------------------------------------------------
    # Rainfall rolling sums
    # Current hour is INCLUDED.
    # --------------------------------------------------------

    windows = {
        1: "Rain_Last_1h",
        3: "Rain_Last_3h",
        6: "Rain_Last_6h",
        12: "Rain_Last_12h",
        24: "Rain_Last_24h",
        72: "Rain_Last_72h",
        168: "Rain_Last_168h",
    }

    for window, column_name in windows.items():

        print(
            f"  Rainfall rolling {window}h..."
        )

        df[column_name] = (
            grouped["Rain_mm"]
            .transform(
                lambda s: s.rolling(
                    window=window,
                    min_periods=window,
                ).sum()
            )
        )

    # --------------------------------------------------------
    # Maximum hourly rainfall
    # --------------------------------------------------------

    print(
        "  Maximum rainfall features..."
    )

    df["Max_Hourly_Rain_Last_6h"] = (
        grouped["Rain_mm"]
        .transform(
            lambda s: s.rolling(
                6,
                min_periods=6,
            ).max()
        )
    )

    df["Max_Hourly_Rain_Last_24h"] = (
        grouped["Rain_mm"]
        .transform(
            lambda s: s.rolling(
                24,
                min_periods=24,
            ).max()
        )
    )

    # --------------------------------------------------------
    # Temperature
    # --------------------------------------------------------

    print(
        "Creating temperature features..."
    )

    df["Temperature_3h_Avg"] = (
        grouped["Temperature_C"]
        .transform(
            lambda s: s.rolling(
                3,
                min_periods=3,
            ).mean()
        )
    )

    df["Temperature_6h_Avg"] = (
        grouped["Temperature_C"]
        .transform(
            lambda s: s.rolling(
                6,
                min_periods=6,
            ).mean()
        )
    )

    # --------------------------------------------------------
    # Humidity
    # --------------------------------------------------------

    print(
        "Creating humidity features..."
    )

    df["Humidity_6h_Avg"] = (
        grouped["Relative_Humidity_pct"]
        .transform(
            lambda s: s.rolling(
                6,
                min_periods=6,
            ).mean()
        )
    )

    # --------------------------------------------------------
    # Wind
    # --------------------------------------------------------

    print(
        "Creating wind features..."
    )

    df["Wind_6h_Avg"] = (
        grouped["Wind_Speed_kmh"]
        .transform(
            lambda s: s.rolling(
                6,
                min_periods=6,
            ).mean()
        )
    )

    # --------------------------------------------------------
    # Solar radiation
    # --------------------------------------------------------

    print(
        "Creating solar radiation features..."
    )

    df["Solar_6h_Sum"] = (
        grouped["Shortwave_Radiation_W_m2"]
        .transform(
            lambda s: s.rolling(
                6,
                min_periods=6,
            ).sum()
        )
    )

    return df


# ============================================================
# HOURS SINCE LAST RAIN
# ============================================================
def create_hours_since_rain(
    df,
    previous_last_rain,
):

    print(
        "Creating Hours_Since_Last_Rain..."
    )

    # --------------------------------------------------------
    # Timestamp of the current hour when rain occurred
    # --------------------------------------------------------

    df["__Rain_Event_Time"] = (
        df["DateTime"].where(
            df["Rain_mm"] > 0
        )
    )

    # Make absolutely sure this is datetime64[ns]
    df["__Rain_Event_Time"] = pd.to_datetime(
        df["__Rain_Event_Time"],
        errors="coerce",
    )

    # --------------------------------------------------------
    # Forward-fill the most recent rain event
    # separately for each location
    # --------------------------------------------------------

    last_event = (
        df.groupby(
            "Location_ID",
            sort=False,
        )["__Rain_Event_Time"]
        .transform("ffill")
    )

    # --------------------------------------------------------
    # For locations where no rain event exists in the
    # current buffer, use the previous month's last event.
    #
    # IMPORTANT:
    # Convert fallback to datetime before combining.
    # --------------------------------------------------------

    if previous_last_rain:

        fallback = pd.to_datetime(
            df["Location_ID"].map(
                previous_last_rain
            ),
            errors="coerce",
        )

        last_event = last_event.where(
            last_event.notna(),
            fallback,
        )

    # Force final dtype to datetime
    last_event = pd.to_datetime(
        last_event,
        errors="coerce",
    )

    # --------------------------------------------------------
    # Calculate hours since last rain
    # --------------------------------------------------------

    time_difference = (
        df["DateTime"] - last_event
    )

    df["Hours_Since_Last_Rain"] = (
        time_difference.dt.total_seconds()
        / 3600.0
    )

    # --------------------------------------------------------
    # Update last-rain state for the next month
    #
    # Use the latest ACTUAL rain event, not simply the last
    # row (because the last row may have zero rainfall).
    # --------------------------------------------------------

    latest_events = (
        df.loc[
            df["__Rain_Event_Time"].notna(),
            [
                "Location_ID",
                "__Rain_Event_Time",
            ],
        ]
        .groupby(
            "Location_ID",
            sort=False,
        )["__Rain_Event_Time"]
        .max()
    )

    for location_id, timestamp in (
        latest_events.items()
    ):

        if pd.notna(timestamp):

            previous_last_rain[
                location_id
            ] = timestamp

    # --------------------------------------------------------
    # Remove temporary column
    # --------------------------------------------------------

    df = df.drop(
        columns=[
            "__Rain_Event_Time"
        ]
    )

    return df


# ============================================================
# STATIC MERGE
# ============================================================

def merge_static_features(
    df,
    static_data,
):

    print(
        "Merging static location features..."
    )

    df = df.merge(
        static_data,
        on="Location_ID",
        how="left",
        validate="many_to_one",
    )

    missing_static = (
        df[STATIC_FEATURES]
        .isna()
        .any(axis=1)
        .sum()
    )

    if missing_static > 0:

        raise RuntimeError(
            f"{missing_static:,} rows have "
            f"missing static features."
        )

    return df


# ============================================================
# TIME FEATURES
# ============================================================

def create_time_features(df):

    print(
        "Creating time features..."
    )

    df["Hour"] = (
        df["DateTime"].dt.hour
    )

    df["Day_of_Week"] = (
        df["DateTime"].dt.dayofweek
    )

    df["Month"] = (
        df["DateTime"].dt.month
    )

    return df


# ============================================================
# PROCESS ONE MONTH
# ============================================================

def process_month(
    year,
    month,
    history_tail,
    previous_last_rain,
    static_data,
):

    print()
    print("=" * 70)
    print(
        f"PROCESSING FEATURES: "
        f"{year}-{month:02d}"
    )
    print("=" * 70)

    current = load_month(
        year,
        month,
    )

    # Mark current rows so history can
    # be removed after rolling calculations.
    current["__Current_Month"] = True

    # --------------------------------------------------------
    # Add history from previous month
    # --------------------------------------------------------

    if history_tail is not None:

        print(
            f"Adding {len(history_tail):,} "
            f"historical buffer rows..."
        )

        history = (
            history_tail.copy()
        )

        history["__Current_Month"] = False

        combined = pd.concat(
            [
                history,
                current,
            ],
            ignore_index=True,
        )

    else:

        print(
            "No previous-month history "
            "(first month)."
        )

        combined = current.copy()

    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    combined = combined.sort_values(
        [
            "Location_ID",
            "DateTime",
        ]
    ).reset_index(
        drop=True
    )

    # --------------------------------------------------------
    # Rolling features
    # --------------------------------------------------------

    combined = create_rolling_features(
        combined
    )

    # --------------------------------------------------------
    # Hours since rain
    # --------------------------------------------------------

    combined = create_hours_since_rain(
        combined,
        previous_last_rain,
    )

    # --------------------------------------------------------
    # Time features
    # --------------------------------------------------------

    combined = create_time_features(
        combined
    )

    # --------------------------------------------------------
    # Keep only current month
    # --------------------------------------------------------

    result = combined[
        combined["__Current_Month"]
    ].copy()

    # --------------------------------------------------------
    # Merge static features
    # --------------------------------------------------------

    result = merge_static_features(
        result,
        static_data,
    )

    # --------------------------------------------------------
    # Full 7-day history indicator
    # --------------------------------------------------------

    result["Full_7d_History"] = (
        result["Rain_Last_168h"]
        .notna()
    )

    # --------------------------------------------------------
    # Final column order
    # --------------------------------------------------------

    output_columns = [
        "Location_ID",
        "DateTime",
        "Latitude",
        "Longitude",

        # Current weather
        "Rain_mm",
        "Temperature_C",
        "Relative_Humidity_pct",
        "Wind_Speed_kmh",
        "Shortwave_Radiation_W_m2",

        # Rainfall persistence
        "Rain_Last_1h",
        "Rain_Last_3h",
        "Rain_Last_6h",
        "Rain_Last_12h",
        "Rain_Last_24h",
        "Rain_Last_72h",
        "Rain_Last_168h",
        "Max_Hourly_Rain_Last_6h",
        "Max_Hourly_Rain_Last_24h",
        "Hours_Since_Last_Rain",

        # Drying
        "Temperature_3h_Avg",
        "Temperature_6h_Avg",
        "Humidity_6h_Avg",
        "Wind_6h_Avg",
        "Solar_6h_Sum",

        # Time
        "Hour",
        "Day_of_Week",
        "Month",

        # Static
        *STATIC_FEATURES,

        # History availability
        "Full_7d_History",
    ]

    result = result[
        output_columns
    ]

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    output_dir = (
        FEATURE_ROOT
        / str(year)
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file = (
        output_dir
        / f"{month:02d}.parquet"
    )

    result.to_parquet(
        output_file,
        engine="pyarrow",
        compression="snappy",
        index=False,
    )

    print()
    print(
        f"✅ Saved:"
    )

    print(
        output_file
    )

    print(
        f"Rows: "
        f"{len(result):,}"
    )

    print(
        f"Columns: "
        f"{len(result.columns)}"
    )

    # --------------------------------------------------------
    # Prepare history tail for next month
    # --------------------------------------------------------

    history_columns = [
        "Location_ID",
        "DateTime",
        "Rain_mm",
        "Temperature_C",
        "Relative_Humidity_pct",
        "Wind_Speed_kmh",
        "Shortwave_Radiation_W_m2",
    ]

    history_tail = (
        result[history_columns]
        .groupby(
            "Location_ID",
            sort=False,
        )
        .tail(LOOKBACK_HOURS)
        .copy()
    )

    return (
        history_tail,
        previous_last_rain,
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("HOURLY FEATURE ENGINEERING")
    print("=" * 70)

    if TEST_MODE:

        print()
        print(
            "⚠️ TEST MODE ENABLED"
        )

        print(
            f"Only processing "
            f"{TEST_YEAR}-{TEST_MONTH:02d}"
        )

    else:

        print()
        print(
            "FULL MODE: Processing "
            "2021–2025"
        )

    # --------------------------------------------------------
    # Load static locations
    # --------------------------------------------------------

    static_data = load_static_data()

    print(
        f"✅ Static locations loaded: "
        f"{len(static_data)}"
    )

    # --------------------------------------------------------
    # State carried from month to month
    # --------------------------------------------------------

    history_tail = None

    previous_last_rain = {}

    # --------------------------------------------------------
    # Determine processing range
    # --------------------------------------------------------

    if TEST_MODE:

        months_to_process = [
            (
                TEST_YEAR,
                TEST_MONTH,
            )
        ]

    else:

        months_to_process = []

        for year in range(
            START_YEAR,
            END_YEAR + 1,
        ):

            for month in range(
                1,
                13,
            ):

                months_to_process.append(
                    (
                        year,
                        month,
                    )
                )

    # --------------------------------------------------------
    # Process
    # --------------------------------------------------------

    for year, month in (
        months_to_process
    ):

        (
            history_tail,
            previous_last_rain,
        ) = process_month(
            year,
            month,
            history_tail,
            previous_last_rain,
            static_data,
        )

    print()
    print("=" * 70)

    if TEST_MODE:

        print(
            "✅ TEST FEATURE ENGINEERING COMPLETE"
        )

        print()
        print(
            "Inspect the generated file before "
            "switching TEST_MODE to False."
        )

    else:

        print(
            "✅ FULL FEATURE ENGINEERING COMPLETE"
        )

    print("=" * 70)


if __name__ == "__main__":
    main()