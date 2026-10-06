from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import time

import numpy as np
import pandas as pd
import requests


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent

STATIC_FILE = (
    PROJECT_ROOT
    / "data"
    / "static_locations.csv"
)

LIVE_OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "live"
)

LIVE_OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# OPEN-METEO
# ============================================================

OPEN_METEO_URL = (
    "https://api.open-meteo.com/v1/forecast"
)

TIMEZONE = "Asia/Kolkata"

BATCH_SIZE = 25
# We need 168 hours for the longest rolling feature.
# 1200 hours gives enough history for
# Hours_Since_Last_Rain during long dry periods.
BATCH_DELAY_SECONDS = 2.0

PAST_HOURS = 168

# Current-risk model does NOT use future forecast values.
# One forecast hour is requested only to ensure the
# current hourly observation is available reliably.
FORECAST_HOURS = 1

# Process all 482 locations for the live application.
TEST_LOCATION_LIMIT = None
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
# FINAL 34 ML FEATURES
# MUST MATCH TRAINING ORDER EXACTLY
# ============================================================

MODEL_FEATURES = [
    "Latitude",
    "Longitude",

    "Rain_mm",
    "Temperature_C",
    "Relative_Humidity_pct",
    "Wind_Speed_kmh",
    "Shortwave_Radiation_W_m2",

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

    "Temperature_3h_Avg",
    "Temperature_6h_Avg",
    "Humidity_6h_Avg",
    "Wind_6h_Avg",
    "Solar_6h_Sum",

    "Hour",
    "Day_of_Week",
    "Month",

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
# HTTP SESSION
# ============================================================

session = requests.Session()

session.headers.update({
    "User-Agent": "Pune-Hyperlocal-Waterlogging-ML/1.0"
})

# ============================================================
# API THROTTLING
# ============================================================

API_REQUEST_INTERVAL_SECONDS = 2.0

_last_api_request_at = 0.0

# ============================================================
# LOAD STATIC LOCATIONS
# ============================================================

def load_locations() -> pd.DataFrame:

    if not STATIC_FILE.exists():
        raise FileNotFoundError(
            f"Static locations file not found:\n"
            f"{STATIC_FILE}"
        )

    locations = pd.read_csv(STATIC_FILE)

    # --------------------------------------------------------
    # Create Location_ID if necessary
    # --------------------------------------------------------

    if "Location_ID" not in locations.columns:

        required = [
            "Ward_Name",
            "Point_ID",
        ]

        missing = [
            c for c in required
            if c not in locations.columns
        ]

        if missing:
            raise ValueError(
                "Cannot create Location_ID. "
                f"Missing columns: {missing}"
            )

        locations["Location_ID"] = (
            locations["Ward_Name"]
            .astype(str)
            .str.strip()
            + "__"
            + locations["Point_ID"]
            .astype(str)
            .str.strip()
        )

    # --------------------------------------------------------
    # Remove duplicate physical locations
    # --------------------------------------------------------

    locations = (
        locations
        .drop_duplicates(
            subset=["Location_ID"]
        )
        .reset_index(drop=True)
    )

    print(
        f"Unique physical locations found: "
        f"{len(locations)}"
    )

    # --------------------------------------------------------
    # Required columns
    # --------------------------------------------------------

    required_columns = [
        "Location_ID",
        "Latitude",
        "Longitude",
        *STATIC_FEATURES,
    ]

    missing = [
        c for c in required_columns
        if c not in locations.columns
    ]

    if missing:
        raise ValueError(
            "Missing required columns in "
            f"static_locations.csv:\n{missing}"
        )

    # --------------------------------------------------------
    # Numeric conversion
    # --------------------------------------------------------

    numeric_columns = [
        "Latitude",
        "Longitude",
        *STATIC_FEATURES,
    ]

    for column in numeric_columns:

        locations[column] = pd.to_numeric(
            locations[column],
            errors="coerce"
        )

    # --------------------------------------------------------
    # No missing static values
    # --------------------------------------------------------

    missing_counts = (
        locations[
            numeric_columns
        ]
        .isna()
        .sum()
    )

    bad_columns = (
        missing_counts[
            missing_counts > 0
        ]
    )

    if not bad_columns.empty:

        raise ValueError(
            "Missing/non-numeric static values:\n"
            + bad_columns.to_string()
        )

    return locations


# ============================================================
# FETCH ONE BATCH
# ============================================================

def fetch_batch(
    locations: pd.DataFrame
):

    latitudes = ",".join(
        locations["Latitude"]
        .astype(float)
        .astype(str)
        .tolist()
    )

    longitudes = ",".join(
        locations["Longitude"]
        .astype(float)
        .astype(str)
        .tolist()
    )

    params = {

        "latitude": latitudes,

        "longitude": longitudes,

        "hourly": (
            "rain,"
            "temperature_2m,"
            "relative_humidity_2m,"
            "wind_speed_10m,"
            "shortwave_radiation"
        ),

        "past_hours": PAST_HOURS,

        "forecast_hours": FORECAST_HOURS,

        "timezone": TIMEZONE,

        "temperature_unit": "celsius",

        "wind_speed_unit": "kmh",

        "precipitation_unit": "mm",

    }

    max_attempts = 5

    for attempt in range(
        1,
        max_attempts + 1
    ):

        try:

            print(
                f"  API attempt "
                f"{attempt}/{max_attempts}"
            )

            global _last_api_request_at

            elapsed = (
                    time.time()
                    - _last_api_request_at
            )

            wait_time = (
                    API_REQUEST_INTERVAL_SECONDS
                    - elapsed
            )

            if wait_time > 0:
                time.sleep(wait_time)

            response = session.get(
                OPEN_METEO_URL,
                params=params,
                timeout=120,
            )

            _last_api_request_at = time.time()

            # ------------------------------------------------
            # Rate limit
            # ------------------------------------------------

            if response.status_code == 429:

                retry_after = (
                    response
                    .headers
                    .get("Retry-After")
                )

                if retry_after:
                    try:
                        wait_seconds = int(
                            retry_after
                        )
                    except ValueError:
                        wait_seconds = 60
                else:
                    wait_seconds = (
                        30 * attempt
                    )

                print(
                    "  Open-Meteo rate limit. "
                    f"Waiting {wait_seconds}s..."
                )

                time.sleep(
                    wait_seconds
                )

                continue

            response.raise_for_status()

            payload = response.json()

            # Multiple coordinates return a list.
            if not isinstance(
                payload,
                list
            ):
                payload = [payload]

            if len(payload) != len(
                locations
            ):
                raise RuntimeError(
                    f"Requested "
                    f"{len(locations)} locations, "
                    f"received "
                    f"{len(payload)} responses."
                )

            return payload

        except requests.RequestException as exc:

            print(
                f"  Request failed: {exc}"
            )

            if attempt == max_attempts:
                raise

            wait_seconds = (
                10 * attempt
            )

            time.sleep(
                wait_seconds
            )

    raise RuntimeError(
        "Open-Meteo request failed."
    )


# ============================================================
# CONVERT RESPONSE TO DATAFRAME
# ============================================================

def response_to_dataframe(
    location: pd.Series,
    weather_response: dict,
) -> pd.DataFrame:

    hourly = weather_response.get(
        "hourly"
    )

    if hourly is None:
        raise ValueError(
            "Open-Meteo response has no hourly data."
        )

    required = [
        "time",
        "rain",
        "temperature_2m",
        "relative_humidity_2m",
        "wind_speed_10m",
        "shortwave_radiation",
    ]

    missing = [
        c
        for c in required
        if c not in hourly
    ]

    if missing:
        raise ValueError(
            "Missing Open-Meteo hourly variables: "
            + ", ".join(missing)
        )

    frame = pd.DataFrame({

        "DateTime": pd.to_datetime(
            hourly["time"],
            errors="coerce"
        ),

        "Rain_mm": pd.to_numeric(
            hourly["rain"],
            errors="coerce"
        ),

        "Temperature_C": pd.to_numeric(
            hourly["temperature_2m"],
            errors="coerce"
        ),

        "Relative_Humidity_pct": pd.to_numeric(
            hourly["relative_humidity_2m"],
            errors="coerce"
        ),

        "Wind_Speed_kmh": pd.to_numeric(
            hourly["wind_speed_10m"],
            errors="coerce"
        ),

        "Shortwave_Radiation_W_m2": pd.to_numeric(
            hourly["shortwave_radiation"],
            errors="coerce"
        ),

    })

    # Open-Meteo timestamps are local because
    # timezone=Asia/Kolkata was requested.
    frame["DateTime"] = (
        frame["DateTime"]
        .dt
        .tz_localize(TIMEZONE)
    )

    # --------------------------------------------------------
    # Cleaning
    # --------------------------------------------------------

    frame["Rain_mm"] = (
        frame["Rain_mm"]
        .fillna(0)
        .clip(lower=0)
    )

    numeric_weather = [
        "Temperature_C",
        "Relative_Humidity_pct",
        "Wind_Speed_kmh",
        "Shortwave_Radiation_W_m2",
    ]

    for column in numeric_weather:

        frame[column] = (
            frame[column]
            .replace(
                [np.inf, -np.inf],
                np.nan
            )
        )

    # --------------------------------------------------------
    # Only use weather up to the current time.
    #
    # Future forecast values are NEVER features.
    # --------------------------------------------------------

    now = datetime.now(
        ZoneInfo(TIMEZONE)
    )

    current_time = pd.Timestamp(now)

    frame = (
        frame[
            frame["DateTime"]
            <= current_time
        ]
        .copy()
    )

    if frame.empty:
        raise ValueError(
            "No current/past weather data returned."
        )

    frame = frame.sort_values(
        "DateTime"
    ).reset_index(
        drop=True
    )

    # --------------------------------------------------------
    # Verify hourly continuity
    # --------------------------------------------------------

    deltas = (
        frame["DateTime"]
        .diff()
        .dropna()
    )

    if not (
        deltas
        == pd.Timedelta(hours=1)
    ).all():

        raise ValueError(
            "Hourly weather history is not continuous."
        )

    return frame


# ============================================================
# CALCULATE LIVE FEATURES
# ============================================================

def calculate_features(
    weather: pd.DataFrame,
) -> dict:

    required_history = 168

    if len(weather) < required_history:
        raise ValueError(
            f"Only {len(weather)} hourly rows available; "
            f"need at least {required_history}."
        )

    weather = weather.copy()

    # ========================================================
    # RAINFALL PERSISTENCE
    # ========================================================

    weather["Rain_Last_1h"] = (
        weather["Rain_mm"]
        .rolling(
            window=1,
            min_periods=1
        )
        .sum()
    )

    weather["Rain_Last_3h"] = (
        weather["Rain_mm"]
        .rolling(
            window=3,
            min_periods=3
        )
        .sum()
    )

    weather["Rain_Last_6h"] = (
        weather["Rain_mm"]
        .rolling(
            window=6,
            min_periods=6
        )
        .sum()
    )

    weather["Rain_Last_12h"] = (
        weather["Rain_mm"]
        .rolling(
            window=12,
            min_periods=12
        )
        .sum()
    )

    weather["Rain_Last_24h"] = (
        weather["Rain_mm"]
        .rolling(
            window=24,
            min_periods=24
        )
        .sum()
    )

    weather["Rain_Last_72h"] = (
        weather["Rain_mm"]
        .rolling(
            window=72,
            min_periods=72
        )
        .sum()
    )

    weather["Rain_Last_168h"] = (
        weather["Rain_mm"]
        .rolling(
            window=168,
            min_periods=168
        )
        .sum()
    )

    # ========================================================
    # RAINFALL PEAKS
    # ========================================================

    weather["Max_Hourly_Rain_Last_6h"] = (
        weather["Rain_mm"]
        .rolling(
            window=6,
            min_periods=6
        )
        .max()
    )

    weather["Max_Hourly_Rain_Last_24h"] = (
        weather["Rain_mm"]
        .rolling(
            window=24,
            min_periods=24
        )
        .max()
    )

    # ========================================================
    # HOURS SINCE LAST RAIN
    # ========================================================

    rain_occurrence = (
        weather["Rain_mm"]
        > 0
    )

    rain_index = pd.Series(
        np.where(
            rain_occurrence,
            np.arange(len(weather)),
            np.nan
        ),
        index=weather.index
    )

    last_rain_index = (
        rain_index
        .ffill()
    )

    weather["Hours_Since_Last_Rain"] = (
        np.arange(len(weather))
        - last_rain_index
    )

    # If no rain occurred inside our available
    # history, represent at least the full history.
    weather[
        "Hours_Since_Last_Rain"
    ] = (
        weather[
            "Hours_Since_Last_Rain"
        ]
        .fillna(PAST_HOURS)
    )

    # ========================================================
    # DRYING FEATURES
    # ========================================================

    weather["Temperature_3h_Avg"] = (
        weather["Temperature_C"]
        .rolling(
            window=3,
            min_periods=3
        )
        .mean()
    )

    weather["Temperature_6h_Avg"] = (
        weather["Temperature_C"]
        .rolling(
            window=6,
            min_periods=6
        )
        .mean()
    )

    weather["Humidity_6h_Avg"] = (
        weather["Relative_Humidity_pct"]
        .rolling(
            window=6,
            min_periods=6
        )
        .mean()
    )

    weather["Wind_6h_Avg"] = (
        weather["Wind_Speed_kmh"]
        .rolling(
            window=6,
            min_periods=6
        )
        .mean()
    )

    weather["Solar_6h_Sum"] = (
        weather["Shortwave_Radiation_W_m2"]
        .rolling(
            window=6,
            min_periods=6
        )
        .sum()
    )

    # ========================================================
    # TIME FEATURES
    # ========================================================

    weather["Hour"] = (
        weather["DateTime"]
        .dt.hour
    )

    weather["Day_of_Week"] = (
        weather["DateTime"]
        .dt.dayofweek
    )

    weather["Month"] = (
        weather["DateTime"]
        .dt.month
    )

    # ========================================================
    # CURRENT ROW
    # ========================================================

    current = weather.iloc[-1]

    values = {

        "Rain_mm":
            current["Rain_mm"],

        "Temperature_C":
            current["Temperature_C"],

        "Relative_Humidity_pct":
            current[
                "Relative_Humidity_pct"
            ],

        "Wind_Speed_kmh":
            current["Wind_Speed_kmh"],

        "Shortwave_Radiation_W_m2":
            current[
                "Shortwave_Radiation_W_m2"
            ],

        "Rain_Last_1h":
            current["Rain_Last_1h"],

        "Rain_Last_3h":
            current["Rain_Last_3h"],

        "Rain_Last_6h":
            current["Rain_Last_6h"],

        "Rain_Last_12h":
            current["Rain_Last_12h"],

        "Rain_Last_24h":
            current["Rain_Last_24h"],

        "Rain_Last_72h":
            current["Rain_Last_72h"],

        "Rain_Last_168h":
            current["Rain_Last_168h"],

        "Max_Hourly_Rain_Last_6h":
            current[
                "Max_Hourly_Rain_Last_6h"
            ],

        "Max_Hourly_Rain_Last_24h":
            current[
                "Max_Hourly_Rain_Last_24h"
            ],

        "Hours_Since_Last_Rain":
            current[
                "Hours_Since_Last_Rain"
            ],

        "Temperature_3h_Avg":
            current["Temperature_3h_Avg"],

        "Temperature_6h_Avg":
            current["Temperature_6h_Avg"],

        "Humidity_6h_Avg":
            current["Humidity_6h_Avg"],

        "Wind_6h_Avg":
            current["Wind_6h_Avg"],

        "Solar_6h_Sum":
            current["Solar_6h_Sum"],

        "Hour":
            current["Hour"],

        "Day_of_Week":
            current["Day_of_Week"],

        "Month":
            current["Month"],

        "DateTime":
            current["DateTime"],

    }

    # ========================================================
    # VALIDATION
    # ========================================================

    for key, value in values.items():

        if key == "DateTime":
            continue

        if not np.isfinite(
            float(value)
        ):
            raise ValueError(
                f"Invalid feature value "
                f"for {key}: {value}"
            )

    return values

# ============================================================
# PROCESS ONE LOCATION
# ============================================================

def process_location(
    location: pd.Series,
    weather_response: dict,
) -> dict:

    weather = response_to_dataframe(
        location,
        weather_response
    )

    features = calculate_features(
        weather
    )

    result = {

        "Location_ID":
            location["Location_ID"],

        "Ward_Name":
            location.get(
                "Ward_Name",
                ""
            ),

        "Point_ID":
            location.get(
                "Point_ID",
                ""
            ),

        "DateTime":
            features.pop("DateTime"),

        "Latitude":
            float(
                location["Latitude"]
            ),

        "Longitude":
            float(
                location["Longitude"]
            ),

        **features,
    }

    # --------------------------------------------------------
    # Add static location features
    # --------------------------------------------------------

    for column in STATIC_FEATURES:

        result[column] = float(
            location[column]
        )

    return result

# ============================================================
# MAIN PIPELINE
# ============================================================

def main():

    print()
    print("=" * 80)
    print("LIVE WEATHER → 34-FEATURE PIPELINE")
    print("=" * 80)

    # --------------------------------------------------------
    # LOAD LOCATIONS
    # --------------------------------------------------------

    locations = load_locations()

    # --------------------------------------------------------
    # TEST LIMIT
    # --------------------------------------------------------

    if TEST_LOCATION_LIMIT is not None:

        test_locations = (
            locations
            .head(TEST_LOCATION_LIMIT)
            .copy()
        )

        print(
            f"TEST MODE: processing "
            f"{len(test_locations)} locations"
        )

    else:

        test_locations = locations.copy()

        print(
            f"FULL MODE: processing "
            f"{len(test_locations)} locations"
        )

    # --------------------------------------------------------
    # FETCH AND PROCESS
    # --------------------------------------------------------

    results = []

    total_batches = (
        (
            len(test_locations)
            + BATCH_SIZE
            - 1
        )
        // BATCH_SIZE
    )

    for batch_number, start in enumerate(
        range(
            0,
            len(test_locations),
            BATCH_SIZE
        ),
        start=1
    ):

        batch = test_locations[
            start:
            start + BATCH_SIZE
        ]

        print()
        print(
            f"Batch "
            f"{batch_number}/"
            f"{total_batches} | "
            f"Locations: "
            f"{len(batch)}"
        )

        responses = fetch_batch(
            batch
        )

        for location, response in zip(
            batch.to_dict(
                orient="records"
            ),
            responses
        ):

            location_series = pd.Series(
                location
            )

            try:

                result = process_location(
                    location_series,
                    response
                )

                results.append(
                    result
                )

                print(
                    f"  ✅ "
                    f"{location['Location_ID']}"
                )

            except Exception as exc:

                print(
                    f"  ❌ "
                    f"{location['Location_ID']}: "
                    f"{exc}"
                )

    # --------------------------------------------------------
    # BUILD FINAL DATAFRAME
    # --------------------------------------------------------

    if not results:
        raise RuntimeError(
            "No live feature rows were created."
        )

    final_df = pd.DataFrame(
        results
    )

    # --------------------------------------------------------
    # FEATURE ORDER CHECK
    # --------------------------------------------------------

    missing_features = [
        c
        for c in MODEL_FEATURES
        if c not in final_df.columns
    ]

    if missing_features:

        raise RuntimeError(
            "Missing model features:\n"
            + "\n".join(
                missing_features
            )
        )

    # --------------------------------------------------------
    # CHECK ALL 34 FEATURES
    # --------------------------------------------------------

    feature_matrix = (
        final_df[
            MODEL_FEATURES
        ]
        .copy()
    )

    if feature_matrix.shape[1] != 34:

        raise RuntimeError(
            f"Expected 34 ML features, "
            f"found "
            f"{feature_matrix.shape[1]}"
        )

    missing_values = (
        feature_matrix
        .isna()
        .sum()
    )

    bad_missing = (
        missing_values[
            missing_values > 0
        ]
    )

    if not bad_missing.empty:

        raise RuntimeError(
            "Missing live ML feature values:\n"
            + bad_missing.to_string()
        )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    csv_path = (
        LIVE_OUTPUT_DIR
        / "live_features_latest.csv"
    )

    parquet_path = (
        LIVE_OUTPUT_DIR
        / "live_features_latest.parquet"
    )

    final_df.to_csv(
        csv_path,
        index=False
    )

    final_df.to_parquet(
        parquet_path,
        index=False
    )

    # --------------------------------------------------------
    # REPORT
    # --------------------------------------------------------

    print()
    print("=" * 80)
    print("LIVE PIPELINE TEST COMPLETE")
    print("=" * 80)

    print(
        f"Locations processed : "
        f"{len(final_df)}"
    )

    print(
        f"ML feature count    : "
        f"{len(MODEL_FEATURES)}"
    )

    print(
        f"Current timestamp    : "
        f"{final_df['DateTime'].min()}"
    )

    print()
    print(
        "34 MODEL FEATURES:"
    )

    for i, feature in enumerate(
        MODEL_FEATURES,
        start=1
    ):
        print(
            f"{i:02d}. {feature}"
        )

    print()
    print(
        f"CSV saved     : {csv_path}"
    )

    print(
        f"Parquet saved : {parquet_path}"
    )

    print()
    print(
        "✅ 34-feature live pipeline "
        "passed validation."
    )


if __name__ == "__main__":
    main()