from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json
import math
import threading
import time

import joblib
import numpy as np
import pandas as pd
import requests

from fastapi import HTTPException
from pydantic import BaseModel, Field


# ============================================================
# PATHS
# ============================================================

ROOT_DIR = Path(__file__).resolve().parent

MODEL_PATH = ROOT_DIR / "models" / "current_hourly_waterlogging_hgb_validation.joblib"

LIVE_DIR = ROOT_DIR / "data" / "live"
LIVE_FEATURES_PATH = LIVE_DIR / "live_features_latest.parquet"
LIVE_PREDICTIONS_PATH = LIVE_DIR / "live_predictions_latest.csv"

STATIC_LOCATIONS_PATH = ROOT_DIR / "data" / "static_locations.csv"


# ============================================================
# APPLICATION
# ============================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "https://pune-hyperlocal-waterlogging-risk-1.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# your existing routes below

# ============================================================
# CONFIGURATION
# ============================================================

TIMEZONE = "Asia/Kolkata"

CACHE_SECONDS = 15 * 60
BATCH_SIZE = 25

# Route risk matching radius.
# A modeled waterlogging point within this distance of the route
# is considered relevant to that route.
ROUTE_MATCH_RADIUS_M = 150.0

# ------------------------------------------------------------
# Routing / Geocoding
# ------------------------------------------------------------

ROUTING_URL = "https://router.project-osrm.org/route/v1/driving"

GEOCODING_URL = "https://nominatim.openstreetmap.org/search"

GEOCODING_USER_AGENT = (
    "PuneHyperlocalWaterloggingRisk/1.0 "
    "(educational-research-project)"
)

GEOCODING_MIN_INTERVAL_SECONDS = 1.1


# ============================================================
# MODEL FEATURES
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
# LOAD MODEL
# ============================================================

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"Model file not found: {MODEL_PATH}"
    )

model = joblib.load(MODEL_PATH)


# ============================================================
# CACHE
# ============================================================

_cache_lock = threading.Lock()
_refresh_lock = threading.Lock()

_cached_predictions = None
_cached_at = None


# ============================================================
# GEOCODING CACHE
# ============================================================

_geocode_cache = {}

_geocode_lock = threading.Lock()
_last_geocode_request_at = 0.0


# ============================================================
# REQUEST MODELS
# ============================================================

class RouteRiskRequest(BaseModel):
    start: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Starting address or place",
    )

    destination: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Destination address or place",
    )


# ============================================================
# BASIC HELPERS
# ============================================================

def now_local():
    return datetime.now(
        ZoneInfo(TIMEZONE)
    )


def classify_risk(score):
    score = float(score)

    if score < 30:
        return "LOW"

    if score < 60:
        return "MODERATE"

    if score < 90:
        return "HIGH"

    return "EXTREME"


def cache_is_valid():
    if _cached_predictions is None:
        return False

    if _cached_at is None:
        return False

    age = time.time() - _cached_at

    return age < CACHE_SECONDS


# ============================================================
# LOAD STATIC LOCATIONS
# ============================================================

def load_locations():
    df = pd.read_csv(STATIC_LOCATIONS_PATH)

    # Support the actual static_locations.csv column names
    # used by the project.
    if "Ward" not in df.columns and "Ward_Name" in df.columns:
        df["Ward"] = df["Ward_Name"]

    if "Point" not in df.columns and "Point_ID" in df.columns:
        df["Point"] = df["Point_ID"]

    if "Location_ID" not in df.columns:
        if "Ward_Name" in df.columns and "Point_ID" in df.columns:
            df["Location_ID"] = (
                df["Ward_Name"].astype(str)
                + "__"
                + df["Point_ID"].astype(str)
            )
        elif "Ward" in df.columns and "Point" in df.columns:
            df["Location_ID"] = (
                df["Ward"].astype(str)
                + "__"
                + df["Point"].astype(str)
            )

    required_columns = [
        "Location_ID",
        "Ward",
        "Point",
        "Latitude",
        "Longitude",
    ]

    missing = [c for c in required_columns if c not in df.columns]

    if missing:
        raise ValueError(
            f"Missing columns in static_locations.csv: {missing}"
        )

    return df


# ============================================================
# LIVE WEATHER PIPELINE IMPORT
# ============================================================

try:
    from live_weather_pipeline import (
        fetch_batch,
        process_location,
    )
except ImportError as exc:
    raise ImportError(
        "Could not import fetch_batch/process_location "
        "from live_weather_pipeline.py"
    ) from exc


# ============================================================
# LOAD CACHED PREDICTIONS FROM DISK
# ============================================================

def load_cached_predictions_from_disk():

    global _cached_predictions
    global _cached_at

    if not LIVE_PREDICTIONS_PATH.exists():
        return None

    try:
        # ----------------------------------------------------
        # Check actual age of saved live predictions
        # ----------------------------------------------------

        file_modified_at = (
            LIVE_PREDICTIONS_PATH.stat().st_mtime
        )

        file_age = (
            time.time()
            - file_modified_at
        )

        # Do not use stale predictions
        if file_age >= CACHE_SECONDS:
            return None

        df = pd.read_csv(
            LIVE_PREDICTIONS_PATH
        )

        required = [
            "Location_ID",
            "Ward",
            "Point",
            "Latitude",
            "Longitude",
            "Risk Score",
            "risk_score",
            "risk_level",
            "Rainfall Now",
        ]

        missing = [
            col
            for col in required
            if col not in df.columns
        ]

        if missing:
            return None

        with _cache_lock:

            _cached_predictions = df

            # Preserve the real age of the cached file
            _cached_at = file_modified_at

        return df

    except Exception:
        return None

# ============================================================
# FETCH LIVE FEATURES
# ============================================================

def fetch_live_features():

    locations = load_locations()

    all_features = []

    total = len(locations)

    for start in range(
        0,
        total,
        BATCH_SIZE,
    ):

        batch = locations.iloc[
            start:start + BATCH_SIZE
        ].copy()

        # Fetch Open-Meteo data for this batch.
        # fetch_batch() returns responses in
        # exactly the same order as the locations.
        weather_data = fetch_batch(batch)

        for (_, location), weather in zip(
            batch.iterrows(),
            weather_data,
        ):

            location_id = location["Location_ID"]

            try:

                features = process_location(
                    location,
                    weather,
                )

                all_features.append(
                    features
                )

            except Exception as exc:

                print(
                    f"Failed processing "
                    f"{location_id}: {exc}"
                )

    if not all_features:
        raise RuntimeError(
            "No live features were generated."
        )

    df = pd.DataFrame(
        all_features
    )

    missing_features = [
        col
        for col in MODEL_FEATURES
        if col not in df.columns
    ]

    if missing_features:
        raise ValueError(
            "Missing model features: "
            f"{missing_features}"
        )

    nan_columns = [
        col
        for col in MODEL_FEATURES
        if df[col].isna().any()
    ]

    if nan_columns:
        raise ValueError(
            "NaN values found in model features: "
            f"{nan_columns}"
        )

    return df

# ============================================================
# GENERATE PREDICTIONS
# ============================================================

def generate_predictions(features):
    X = (
        features[
            MODEL_FEATURES
        ]
        .to_numpy(dtype=float)
    )

    predictions = model.predict(X)

    predictions = np.clip(
        predictions,
        0,
        100,
    )

    output = features.copy()

    output["Risk Score"] = predictions
    output["risk_score"] = predictions

    output["risk_level"] = [
        classify_risk(score)
        for score in predictions
    ]

    # --------------------------------------------------------
    # User-friendly output names
    # --------------------------------------------------------

    rename_map = {
        "Rain_mm": "Rainfall Now",
        "Temperature_C": "Temperature",
        "Relative_Humidity_pct": "Humidity",
        "Wind_Speed_kmh": "Wind Speed",
        "Rain_Last_3h": "Rain Last 3h",
        "Rain_Last_24h": "Rain Last 24h",
        "Rain_Last_72h": "Rain Last 72h",
    }

    for source, target in rename_map.items():

        if source in output.columns:
            output[target] = output[source]

    # --------------------------------------------------------
    # Date/time
    # --------------------------------------------------------

    if "DateTime" not in output.columns:

        output["DateTime"] = (
            now_local().isoformat()
        )

    return output


# ============================================================
# REFRESH PREDICTIONS
# ============================================================

def refresh_predictions(
    force=False
):

    global _cached_predictions
    global _cached_at

    with _refresh_lock:

        # ----------------------------------------------------
        # Reuse valid in-memory cache
        # ----------------------------------------------------

        if (
            not force
            and cache_is_valid()
        ):

            return _cached_predictions

        # ----------------------------------------------------
        # Reuse disk cache
        # ----------------------------------------------------

        if not force:

            disk_data = (
                load_cached_predictions_from_disk()
            )

            if disk_data is not None:
                return disk_data

        # ----------------------------------------------------
        # Fetch fresh live data
        # ----------------------------------------------------

        print(
            "Fetching fresh live weather data..."
        )

        features = fetch_live_features()

        predictions = generate_predictions(
            features
        )

        LIVE_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        # ----------------------------------------------------
        # Save features
        # ----------------------------------------------------

        features.to_parquet(
            LIVE_FEATURES_PATH,
            index=False,
        )

        # ----------------------------------------------------
        # Save predictions
        # ----------------------------------------------------

        predictions.to_csv(
            LIVE_PREDICTIONS_PATH,
            index=False,
        )

        with _cache_lock:

            _cached_predictions = predictions
            _cached_at = time.time()

        print(
            "Live predictions refreshed."
        )

        return predictions


# ============================================================
# GET CURRENT PREDICTIONS
# ============================================================

def get_current_predictions():

    global _cached_predictions

    if cache_is_valid():

        return _cached_predictions

    disk_data = (
        load_cached_predictions_from_disk()
    )

    if disk_data is not None:

        return disk_data

    return refresh_predictions(
        force=False
    )


# ============================================================
# ROUTE / GEOGRAPHIC HELPERS
# ============================================================

def haversine_distance_m(
    lat1,
    lon1,
    lat2,
    lon2,
):

    R = 6371000.0

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    dphi = math.radians(
        lat2 - lat1
    )

    dlambda = math.radians(
        lon2 - lon1
    )

    a = (
        math.sin(dphi / 2) ** 2
        +
        math.cos(phi1)
        *
        math.cos(phi2)
        *
        math.sin(dlambda / 2) ** 2
    )

    return (
        2
        * R
        * math.atan2(
            math.sqrt(a),
            math.sqrt(1 - a),
        )
    )


# ============================================================
# DISTANCE FROM A POINT TO ROUTE POLYLINE
# ============================================================

def point_to_route_distance_m(
    lat,
    lon,
    route_coordinates,
):

    if not route_coordinates:
        return float("inf")

    if len(route_coordinates) == 1:

        route_lon, route_lat = (
            route_coordinates[0]
        )

        return haversine_distance_m(
            lat,
            lon,
            route_lat,
            route_lon,
        )

    # --------------------------------------------------------
    # Local equirectangular projection.
    # Pune routes are small enough that this is accurate
    # enough for a 150 m matching radius.
    # --------------------------------------------------------

    lat0 = math.radians(lat)

    scale_x = (
        111320.0
        * math.cos(lat0)
    )

    scale_y = 110540.0

    route = np.asarray(
        route_coordinates,
        dtype=float,
    )

    x1 = (
        route[:-1, 0] - lon
    ) * scale_x

    y1 = (
        route[:-1, 1] - lat
    ) * scale_y

    x2 = (
        route[1:, 0] - lon
    ) * scale_x

    y2 = (
        route[1:, 1] - lat
    ) * scale_y

    dx = x2 - x1
    dy = y2 - y1

    denominator = (
        dx * dx
        +
        dy * dy
    )

    denominator[
        denominator == 0
    ] = 1e-12

    # Projection of origin onto segment.
    t = (
        -(x1 * dx + y1 * dy)
        / denominator
    )

    t = np.clip(
        t,
        0.0,
        1.0,
    )

    closest_x = (
        x1 + t * dx
    )

    closest_y = (
        y1 + t * dy
    )

    distances = np.sqrt(
        closest_x ** 2
        +
        closest_y ** 2
    )

    return float(
        np.min(distances)
    )


# ============================================================
# GEOCODING
# ============================================================

def geocode_place(query):

    global _last_geocode_request_at

    normalized = (
        query
        .strip()
        .lower()
    )

    if not normalized:
        raise HTTPException(
            status_code=400,
            detail="Location cannot be empty.",
        )

    # --------------------------------------------------------
    # Cache first
    # --------------------------------------------------------

    with _geocode_lock:

        if normalized in _geocode_cache:

            return _geocode_cache[
                normalized
            ]

        # ----------------------------------------------------
        # Respect public Nominatim request interval.
        # ----------------------------------------------------

        elapsed = (
            time.time()
            - _last_geocode_request_at
        )

        wait_time = (
            GEOCODING_MIN_INTERVAL_SECONDS
            - elapsed
        )

        if wait_time > 0:
            time.sleep(
                wait_time
            )

        search_query = (
            f"{query}, "
            "Pune, Maharashtra, India"
        )

        try:

            response = requests.get(
                GEOCODING_URL,
                params={
                    "q": search_query,
                    "format": "jsonv2",
                    "limit": 1,
                    "countrycodes": "in",
                },
                headers={
                    "User-Agent":
                        GEOCODING_USER_AGENT
                },
                timeout=15,
            )

            _last_geocode_request_at = (
                time.time()
            )

        except requests.RequestException as exc:

            raise HTTPException(
                status_code=502,
                detail=(
                    "Geocoding service could "
                    f"not be reached: {exc}"
                ),
            )

        if response.status_code != 200:

            raise HTTPException(
                status_code=502,
                detail=(
                    "Geocoding service returned "
                    f"HTTP {response.status_code}."
                ),
            )

        try:
            results = response.json()
        except Exception:

            raise HTTPException(
                status_code=502,
                detail=(
                    "Invalid response from "
                    "geocoding service."
                ),
            )

        if not results:

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Could not find location: "
                    f"{query}"
                ),
            )

        result = results[0]

        try:

            location = {
                "latitude": float(
                    result["lat"]
                ),
                "longitude": float(
                    result["lon"]
                ),
                "display_name": result.get(
                    "display_name",
                    query,
                ),
            }

        except (
            KeyError,
            TypeError,
            ValueError,
        ):

            raise HTTPException(
                status_code=502,
                detail=(
                    "Geocoding response did "
                    "not contain valid coordinates."
                ),
            )

        _geocode_cache[
            normalized
        ] = location

        return location


# ============================================================
# ROUTING
# ============================================================

def get_driving_route(
    start_lat,
    start_lon,
    destination_lat,
    destination_lon,
):

    coordinates = (
        f"{start_lon},{start_lat};"
        f"{destination_lon},{destination_lat}"
    )

    url = (
        f"{ROUTING_URL}/{coordinates}"
    )

    try:

        response = requests.get(
            url,
            params={
                "overview": "full",
                "geometries": "geojson",
                "steps": "false",
                "alternatives": "false",
            },
            timeout=30,
        )

    except requests.RequestException as exc:

        raise HTTPException(
            status_code=502,
            detail=(
                "Routing service could "
                f"not be reached: {exc}"
            ),
        )

    if response.status_code != 200:

        raise HTTPException(
            status_code=502,
            detail=(
                "Routing service returned "
                f"HTTP {response.status_code}."
            ),
        )

    try:

        data = response.json()

    except Exception:

        raise HTTPException(
            status_code=502,
            detail=(
                "Invalid response from "
                "routing service."
            ),
        )

    if data.get("code") != "Ok":

        raise HTTPException(
            status_code=400,
            detail=(
                "No driving route was found "
                "between the selected locations."
            ),
        )

    routes = data.get(
        "routes",
        [],
    )

    if not routes:

        raise HTTPException(
            status_code=400,
            detail=(
                "No driving route was found."
            ),
        )

    route = routes[0]

    geometry = route.get(
        "geometry",
        {},
    )

    route_coordinates = geometry.get(
        "coordinates",
        [],
    )

    if len(route_coordinates) < 2:

        raise HTTPException(
            status_code=502,
            detail=(
                "Routing service returned "
                "an invalid route geometry."
            ),
        )

    return {
        "distance_m": float(
            route.get(
                "distance",
                0,
            )
        ),
        "duration_s": float(
            route.get(
                "duration",
                0,
            )
        ),
        "coordinates": route_coordinates,
    }


# ============================================================
# MATCH WATERLOGGING LOCATIONS TO ROUTE
# ============================================================

def match_route_locations(
    predictions,
    route_coordinates,
):

    matches = []

    for _, row in predictions.iterrows():

        lat = float(
            row["Latitude"]
        )

        lon = float(
            row["Longitude"]
        )

        distance = (
            point_to_route_distance_m(
                lat,
                lon,
                route_coordinates,
            )
        )

        if distance <= ROUTE_MATCH_RADIUS_M:

            matches.append(
                {
                    "Location_ID":
                        row["Location_ID"],

                    "Ward":
                        row["Ward_Name"],

                    "Point":
                        row["Point_ID"],

                    "Latitude":
                        lat,

                    "Longitude":
                        lon,

                    "distance_to_route_m":
                        round(
                            distance,
                            1,
                        ),

                    "risk_score":
                        round(
                            float(
                                row[
                                    "risk_score"
                                ]
                            ),
                            2,
                        ),

                    "risk_level":
                        row[
                            "risk_level"
                        ],

                    "Rainfall Now":
                        round(
                            float(
                                row.get(
                                    "Rainfall Now",
                                    0,
                                )
                            ),
                            2,
                        ),

                    "Rain Last 3h":
                        round(
                            float(
                                row.get(
                                    "Rain Last 3h",
                                    0,
                                )
                            ),
                            2,
                        ),

                    "Rain Last 24h":
                        round(
                            float(
                                row.get(
                                    "Rain Last 24h",
                                    0,
                                )
                            ),
                            2,
                        ),
                }
            )

    matches.sort(
        key=lambda x: (
            -x["risk_score"],
            x["distance_to_route_m"],
        )
    )

    return matches


# ============================================================
# ROUTE RISK AGGREGATION
# ============================================================

def calculate_route_risk(
    matched_locations,
):

    if not matched_locations:

        raise HTTPException(
            status_code=422,
            detail=(
                "No modeled waterlogging "
                "locations were found within "
                f"{ROUTE_MATCH_RADIUS_M:.0f} m "
                "of this route. The route may "
                "be outside the current Pune "
                "risk-model coverage."
            ),
        )

    scores = np.array(
        [
            item["risk_score"]
            for item in matched_locations
        ],
        dtype=float,
    )

    distances = np.array(
        [
            item[
                "distance_to_route_m"
            ]
            for item in matched_locations
        ],
        dtype=float,
    )

    # --------------------------------------------------------
    # Nearby points receive greater influence for the
    # weighted average.
    # --------------------------------------------------------

    weights = 1.0 / (
        distances + 25.0
    )

    weighted_average = float(
        np.sum(
            scores * weights
        )
        /
        np.sum(weights)
    )

    maximum_score = float(
        np.max(scores)
    )

    # --------------------------------------------------------
    # Route risk level is deliberately based on the highest
    # modeled risk location near the route.
    #
    # This avoids hiding a dangerous short section inside
    # an otherwise low-risk route.
    # --------------------------------------------------------

    route_level = classify_risk(
        maximum_score
    )

    high_count = sum(
        item["risk_level"] == "HIGH"
        for item in matched_locations
    )

    extreme_count = sum(
        item["risk_level"] == "EXTREME"
        for item in matched_locations
    )

    moderate_count = sum(
        item["risk_level"] == "MODERATE"
        for item in matched_locations
    )

    low_count = sum(
        item["risk_level"] == "LOW"
        for item in matched_locations
    )

    return {
        "route_risk_score":
            round(
                maximum_score,
                2,
            ),

        "route_risk_level":
            route_level,

        "average_risk_score":
            round(
                weighted_average,
                2,
            ),

        "maximum_risk_score":
            round(
                maximum_score,
                2,
            ),

        "matched_locations":
            len(
                matched_locations
            ),

        "low_locations":
            low_count,

        "moderate_locations":
            moderate_count,

        "high_locations":
            high_count,

        "extreme_locations":
            extreme_count,
    }


# ============================================================
# ROUTE PRECAUTIONS
# ============================================================

def build_route_precautions(
    risk_level
):

    if risk_level == "LOW":

        return [
            "Travel is suitable under the current predicted waterlogging conditions.",
            "Carry a raincoat or waterproof clothing if rain is occurring or expected.",
            "Stay alert for sudden local water accumulation.",
        ]

    if risk_level == "MODERATE":

        return [
            "Travel is possible, but use additional caution.",
            "Carry a raincoat or waterproof clothing.",
            "Reduce speed near low-lying or poorly drained roads.",
            "Avoid entering visibly deep or fast-moving water.",
            "Allow additional travel time.",
        ]

    if risk_level == "HIGH":

        return [
            "Consider delaying travel or using an alternative route.",
            "Carry waterproof clothing if travel is necessary.",
            "Avoid low-lying roads and visibly waterlogged sections.",
            "Do not attempt to cross deep or fast-moving water.",
            "Allow additional travel time and use extra caution.",
        ]

    return [
        "Avoid travel on this route while extreme risk persists.",
        "Consider postponing the journey or choosing another route.",
        "Do not attempt to cross heavily waterlogged roads.",
        "Never enter deep or fast-moving water with a vehicle.",
        "If travel is unavoidable, reassess conditions immediately before departure.",
    ]


# ============================================================
# ROOT
# ============================================================
@app.get("/")
def root():

    return {
        "name":
            "Pune Hyperlocal Current Road-Waterlogging Risk API",

        "version":
            "3.0.0",

        "status":
            "running",

        "risk_type":
            "CURRENT",

        "model":
            "current_hourly_waterlogging_hgb_validation",

        "update_interval_minutes":
            CACHE_SECONDS // 60,

        "location_count":
            len(load_locations()),

        "risk_definition": (
            "Current road-waterlogging risk based on "
            "live weather, recent rainfall persistence, "
            "drying conditions, and location-specific "
            "terrain, drainage, and urban characteristics."
        ),

        "route_risk_endpoint":
            "/api/route-risk",
    }

# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    locations = load_locations()

    return {
        "status":
            "ok",

        "model_loaded":
            model is not None,

        "model_type":
            "CURRENT_RISK",

        "location_count":
            len(locations),

        "timestamp":
            now_local().isoformat(),
    }

# ============================================================
# CURRENT RISK
# ============================================================

@app.get("/api/risk/current")
def current_risk():

    predictions = (
        get_current_predictions()
    )

    return {
        "timestamp":
            now_local().isoformat(),

        "count":
            len(predictions),

        "data":
            predictions.to_dict(
                orient="records"
            ),
    }


# ============================================================
# REFRESH RISK
# ============================================================

@app.get("/api/risk/refresh")
def refresh_risk_get():

    predictions = (
        refresh_predictions(
            force=True
        )
    )

    return {
        "status":
            "refreshed",

        "timestamp":
            now_local().isoformat(),

        "count":
            len(predictions),
    }


@app.post("/api/risk/refresh")
def refresh_risk_post():

    predictions = (
        refresh_predictions(
            force=True
        )
    )

    return {
        "status":
            "refreshed",

        "timestamp":
            now_local().isoformat(),

        "count":
            len(predictions),
    }


# ============================================================
# STATISTICS
# ============================================================

@app.get("/api/risk/stats")
def risk_stats():

    predictions = (
        get_current_predictions()
    )

    counts = (
        predictions[
            "risk_level"
        ]
        .value_counts()
        .to_dict()
    )

    return {
        "total_points":
            len(predictions),

        "low":
            counts.get(
                "LOW",
                0,
            ),

        "moderate":
            counts.get(
                "MODERATE",
                0,
            ),

        "high":
            counts.get(
                "HIGH",
                0,
            ),

        "extreme":
            counts.get(
                "EXTREME",
                0,
            ),

        "average_risk_score":
            round(
                float(
                    predictions[
                        "risk_score"
                    ].mean()
                ),
                2,
            ),

        "current_rainfall":
            round(
                float(
                    predictions[
                        "Rainfall Now"
                    ].mean()
                ),
                2,
            ),

        "timestamp":
            now_local().isoformat(),
    }


# ============================================================
# POINTS
# ============================================================

@app.get("/api/risk/points")
def risk_points():

    predictions = (
        get_current_predictions()
    )

    return {
        "count":
            len(predictions),

        "data":
            predictions.to_dict(
                orient="records"
            ),
    }


# ============================================================
# WARDS
# ============================================================

@app.get("/api/risk/wards")
def risk_wards():

    predictions = (
        get_current_predictions()
    )

    ward_data = []

    for ward, group in predictions.groupby(
        "Ward"
    ):

        max_score = float(
            group[
                "risk_score"
            ].max()
        )

        avg_score = float(
            group[
                "risk_score"
            ].mean()
        )

        ward_data.append(
            {
                "Ward":
                    ward,

                "risk_score":
                    round(
                        max_score,
                        2,
                    ),

                "average_risk_score":
                    round(
                        avg_score,
                        2,
                    ),

                "risk_level":
                    classify_risk(
                        max_score
                    ),

                "points":
                    len(group),
            }
        )

    ward_data.sort(
        key=lambda x:
            x["risk_score"],
        reverse=True,
    )

    return {
        "count":
            len(ward_data),

        "data":
            ward_data,
    }


# ============================================================
# NEAREST POINT
# ============================================================

@app.get("/api/risk/nearest")
def nearest_risk_point(
    latitude: float,
    longitude: float,
):

    predictions = (
        get_current_predictions()
    )

    distances = []

    for _, row in predictions.iterrows():

        distance = (
            haversine_distance_m(
                latitude,
                longitude,
                float(
                    row["Latitude"]
                ),
                float(
                    row["Longitude"]
                ),
            )
        )

        distances.append(
            distance
        )

    index = int(
        np.argmin(
            distances
        )
    )

    result = (
        predictions
        .iloc[index]
        .to_dict()
    )

    result[
        "distance_m"
    ] = round(
        distances[index],
        1,
    )

    return result


# ============================================================
# ROUTE RISK
# ============================================================

@app.post("/api/route-risk")
def route_risk(
    request: RouteRiskRequest
):

    start_query = (
        request.start.strip()
    )

    destination_query = (
        request.destination.strip()
    )

    if (
        start_query.lower()
        ==
        destination_query.lower()
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Start and destination "
                "cannot be the same."
            ),
        )

    # --------------------------------------------------------
    # 1. GEOCODE START
    # --------------------------------------------------------

    start = geocode_place(
        start_query
    )

    # --------------------------------------------------------
    # 2. GEOCODE DESTINATION
    # --------------------------------------------------------

    destination = geocode_place(
        destination_query
    )

    # --------------------------------------------------------
    # 3. GET CURRENT MODEL PREDICTIONS
    # --------------------------------------------------------

    predictions = (
        get_current_predictions()
    )

    # --------------------------------------------------------
    # 4. GET DRIVING ROUTE
    # --------------------------------------------------------

    route = get_driving_route(
        start_lat=
            start["latitude"],

        start_lon=
            start["longitude"],

        destination_lat=
            destination["latitude"],

        destination_lon=
            destination["longitude"],
    )

    # --------------------------------------------------------
    # 5. MATCH MODEL LOCATIONS TO ROUTE
    # --------------------------------------------------------

    matched_locations = (
        match_route_locations(
            predictions,
            route["coordinates"],
        )
    )

    # --------------------------------------------------------
    # 6. CALCULATE ROUTE RISK
    # --------------------------------------------------------

    route_risk_summary = (
        calculate_route_risk(
            matched_locations
        )
    )

    # --------------------------------------------------------
    # 7. PRECAUTIONS
    # --------------------------------------------------------

    precautions = (
        build_route_precautions(
            route_risk_summary[
                "route_risk_level"
            ]
        )
    )

    # --------------------------------------------------------
    # 8. LIMIT LIST OF DISPLAYED POINTS
    # --------------------------------------------------------

    display_locations = (
        matched_locations[:20]
    )

    # --------------------------------------------------------
    # 9. ROUTE RESPONSE
    # --------------------------------------------------------

    return {

        "status":
            "success",

        "timestamp":
            now_local().isoformat(),

        "risk_type":
            "CURRENT",

        # ----------------------------------------------------
        # Start
        # ----------------------------------------------------

        "start": {
            "query":
                start_query,

            "display_name":
                start[
                    "display_name"
                ],

            "latitude":
                start[
                    "latitude"
                ],

            "longitude":
                start[
                    "longitude"
                ],
        },

        # ----------------------------------------------------
        # Destination
        # ----------------------------------------------------

        "destination": {

            "query":
                destination_query,

            "display_name":
                destination[
                    "display_name"
                ],

            "latitude":
                destination[
                    "latitude"
                ],

            "longitude":
                destination[
                    "longitude"
                ],
        },

        # ----------------------------------------------------
        # Route information
        # ----------------------------------------------------

        "route": {

            "distance_m":
                round(
                    route[
                        "distance_m"
                    ],
                    1,
                ),

            "distance_km":
                round(
                    route[
                        "distance_m"
                    ] / 1000.0,
                    2,
                ),

            "duration_seconds":
                round(
                    route[
                        "duration_s"
                    ],
                    0,
                ),

            "duration_minutes":
                round(
                    route[
                        "duration_s"
                    ] / 60.0,
                    1,
                ),

            # GeoJSON-style [longitude, latitude]
            "geometry":
                {
                    "type":
                        "LineString",

                    "coordinates":
                        route[
                            "coordinates"
                        ],
                },
        },

        # ----------------------------------------------------
        # Risk
        # ----------------------------------------------------

        "risk":
            route_risk_summary,

        # ----------------------------------------------------
        # Matched waterlogging locations
        # ----------------------------------------------------

        "risk_locations":
            display_locations,

        # ----------------------------------------------------
        # Precautions
        # ----------------------------------------------------

        "precautions":
            precautions,

        # ----------------------------------------------------
        # Explanation
        # ----------------------------------------------------

        "risk_basis": (
            "Route risk is based on the "
            "highest predicted waterlogging "
            "score among modeled locations "
            f"within {ROUTE_MATCH_RADIUS_M:.0f} m "
            "of the driving route. The "
            "weighted average is also returned "
            "for context."
        ),

        # ----------------------------------------------------
        # Important current limitation
        # ----------------------------------------------------

        "current_risk_note": (
            "This route assessment represents the "
            "current predicted road-waterlogging risk "
            "based on live weather conditions, recent "
            "rainfall history, and location-specific "
            "terrain, drainage, and urban characteristics."
        ),
    }


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
    )