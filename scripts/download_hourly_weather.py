from pathlib import Path
from datetime import date
import time

import pandas as pd
import requests


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent

STATIC_FILE = (
    PROJECT_ROOT
    / "data"
    / "static_locations.csv"
)

OUTPUT_ROOT = (
    PROJECT_ROOT
    / "data"
    / "hourly_raw_historical_forecast"
)

# ------------------------------------------------------------
# Open-Meteo Historical Forecast API
# ------------------------------------------------------------

OPEN_METEO_URL = (
    "https://historical-forecast-api.open-meteo.com/v1/forecast"
)

TIMEZONE = "Asia/Kolkata"


# ============================================================
# FINAL ML YEARS
# ============================================================

START_YEAR = 2021
END_YEAR = 2025

EXPECTED_LOCATION_COUNT = 482


# ============================================================
# DOWNLOAD SETTINGS
# ============================================================

# One request contains 25 physical locations
# for one month.
BATCH_SIZE = 25

# Delay between successful requests.
#
# This is intentionally conservative because
# we already encountered rate limiting.
REQUEST_DELAY_SECONDS = 15

# Maximum retry attempts for a rate-limited request.
MAX_RETRIES = 8


# ============================================================
# HOURLY WEATHER VARIABLES
# ============================================================

HOURLY_VARIABLES = ",".join([
    "rain",
    "temperature_2m",
    "relative_humidity_2m",
    "wind_speed_10m",
    "shortwave_radiation",
])


# ============================================================
# HTTP SESSION
# ============================================================

session = requests.Session()

session.headers.update({
    "User-Agent":
        "Pune-Hyperlocal-Waterlogging-ML/1.0"
})


# ============================================================
# MONTH HELPERS
# ============================================================

def get_month_ranges(year: int):

    months = pd.date_range(
        start=f"{year}-01-01",
        end=f"{year}-12-01",
        freq="MS"
    )

    ranges = []

    for month_start in months:

        month_end = (
            month_start
            + pd.offsets.MonthEnd(1)
        )

        ranges.append(
            (
                month_start.strftime(
                    "%Y-%m-%d"
                ),
                month_end.strftime(
                    "%Y-%m-%d"
                ),
                month_start.strftime(
                    "%m"
                )
            )
        )

    return ranges


# ============================================================
# EXPECTED ROWS
# ============================================================

def expected_rows(
    start_date: str,
    end_date: str,
    location_count: int
) -> int:

    days = pd.date_range(
        start=start_date,
        end=end_date,
        freq="D"
    )

    hours = len(days) * 24

    return (
        len(days)
        * 24
        * location_count
    )


# ============================================================
# VALIDATE SAVED BATCH
# ============================================================

def is_valid_batch_file(
    file_path: Path,
    expected_count: int
) -> bool:

    if not file_path.exists():
        return False

    try:

        actual_count = 0

        for chunk in pd.read_csv(
            file_path,
            compression="gzip",
            usecols=["Location_ID"],
            chunksize=50_000
        ):

            actual_count += len(chunk)

        if actual_count == expected_count:

            return True

        print(
            f"⚠️ Incomplete file detected: "
            f"{file_path.name}"
        )

        print(
            f"   Found: {actual_count:,}"
        )

        print(
            f"   Expected: {expected_count:,}"
        )

        return False

    except Exception as exc:

        print(
            f"⚠️ Could not validate "
            f"{file_path.name}: {exc}"
        )

        return False


# ============================================================
# FETCH ONE MONTH/BATCH
# ============================================================

def fetch_batch(
    locations,
    start_date: str,
    end_date: str
):

    latitudes = ",".join(
        str(
            float(row["Latitude"])
        )
        for row in locations
    )

    longitudes = ",".join(
        str(
            float(row["Longitude"])
        )
        for row in locations
    )


    params = {

        "latitude":
            latitudes,

        "longitude":
            longitudes,

        "start_date":
            start_date,

        "end_date":
            end_date,

        "hourly":
            HOURLY_VARIABLES,

        "timezone":
            TIMEZONE,

        "temperature_unit":
            "celsius",

        "wind_speed_unit":
            "kmh",

        "precipitation_unit":
            "mm",

    }


    for attempt in range(
        1,
        MAX_RETRIES + 1
    ):

        try:

            print(
                f"Request attempt "
                f"{attempt}/{MAX_RETRIES}"
            )


            response = session.get(
                OPEN_METEO_URL,
                params=params,
                timeout=180
            )


            # ------------------------------------------------
            # RATE LIMIT
            # ------------------------------------------------

            if response.status_code == 429:

                retry_after = (
                    response.headers.get(
                        "Retry-After"
                    )
                )


                if retry_after:

                    try:

                        wait_seconds = int(
                            retry_after
                        )

                    except ValueError:

                        wait_seconds = (
                            60 * attempt
                        )

                else:

                    wait_seconds = (
                        60 * attempt
                    )


                print(
                    "⚠️ Open-Meteo rate limit."
                )

                print(
                    f"Waiting "
                    f"{wait_seconds} seconds..."
                )


                time.sleep(
                    wait_seconds
                )

                continue


            # ------------------------------------------------
            # SERVER ERRORS
            # ------------------------------------------------

            if response.status_code >= 500:

                wait_seconds = (
                    30 * attempt
                )

                print(
                    f"⚠️ Open-Meteo server error "
                    f"{response.status_code}."
                )

                print(
                    f"Waiting "
                    f"{wait_seconds} seconds..."
                )


                time.sleep(
                    wait_seconds
                )

                continue


            response.raise_for_status()


            payload = response.json()


            # ------------------------------------------------
            # MULTIPLE COORDINATES
            # ------------------------------------------------

            if isinstance(
                payload,
                dict
            ):

                payload = [
                    payload
                ]


            if not isinstance(
                payload,
                list
            ):

                raise RuntimeError(
                    "Unexpected Open-Meteo response."
                )


            if len(payload) != len(
                locations
            ):

                raise RuntimeError(
                    "Open-Meteo returned "
                    f"{len(payload)} locations, "
                    f"but "
                    f"{len(locations)} "
                    "were requested."
                )


            return payload


        except requests.RequestException as exc:

            print(
                f"⚠️ Request failed: {exc}"
            )


            if attempt == MAX_RETRIES:

                raise


            wait_seconds = (
                30 * attempt
            )


            print(
                f"Waiting "
                f"{wait_seconds} seconds..."
            )


            time.sleep(
                wait_seconds
            )


    raise RuntimeError(
        "Open-Meteo request failed after "
        "all retry attempts."
    )


# ============================================================
# CONVERT RESPONSE TO DATAFRAME
# ============================================================

def response_to_dataframe(
    location,
    weather_response
):

    hourly = weather_response.get(
        "hourly"
    )


    if hourly is None:

        raise ValueError(
            "Missing hourly data."
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

        name

        for name in required

        if name not in hourly

    ]


    if missing:

        raise ValueError(
            "Missing hourly variables: "
            + ", ".join(missing)
        )


    frame = pd.DataFrame({

        "Location_ID":
            location["Location_ID"],

        "Ward_Name":
            location["Ward_Name"],

        "Point_ID":
            location["Point_ID"],

        "Latitude":
            float(
                location["Latitude"]
            ),

        "Longitude":
            float(
                location["Longitude"]
            ),

        "DateTime":
            pd.to_datetime(
                hourly["time"],
                errors="coerce"
            ),

        "Rain_mm":
            pd.to_numeric(
                hourly["rain"],
                errors="coerce"
            ),

        "Temperature_C":
            pd.to_numeric(
                hourly["temperature_2m"],
                errors="coerce"
            ),

        "Humidity_Percent":
            pd.to_numeric(
                hourly["relative_humidity_2m"],
                errors="coerce"
            ),

        "Wind_Speed_kmh":
            pd.to_numeric(
                hourly["wind_speed_10m"],
                errors="coerce"
            ),

        "Shortwave_Radiation_Wm2":
            pd.to_numeric(
                hourly[
                    "shortwave_radiation"
                ],
                errors="coerce"
            ),

    })


    # ========================================================
    # CLEAN NUMERICAL VALUES
    # ========================================================

    numeric_columns = [

        "Rain_mm",

        "Temperature_C",

        "Humidity_Percent",

        "Wind_Speed_kmh",

        "Shortwave_Radiation_Wm2",

    ]


    for column in numeric_columns:

        frame[column] = pd.to_numeric(
            frame[column],
            errors="coerce"
        )


    frame["Rain_mm"] = (
        frame["Rain_mm"]
        .fillna(0)
        .clip(lower=0)
    )


    # ========================================================
    # LOCAL TIME
    # ========================================================

    frame["DateTime"] = (
        frame["DateTime"]
        .dt
        .tz_localize(
            TIMEZONE
        )
    )


    # ========================================================
    # VALIDATION
    # ========================================================

    if frame["DateTime"].isna().any():

        raise ValueError(
            "Invalid DateTime values found."
        )


    return frame


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)

    print(
        "HOURLY HISTORICAL FORECAST "
        "WEATHER DOWNLOAD"
    )

    print("=" * 70)


    # ========================================================
    # STATIC LOCATIONS
    # ========================================================

    if not STATIC_FILE.exists():

        raise FileNotFoundError(
            f"Static locations file not found:\n"
            f"{STATIC_FILE}"
        )


    locations = pd.read_csv(
        STATIC_FILE
    )


    required_columns = [

        "Ward_Name",

        "Point_ID",

        "Latitude",

        "Longitude",

    ]


    for column in required_columns:

        if column not in locations.columns:

            raise ValueError(
                f"Missing column: "
                f"{column}"
            )


    # ========================================================
    # LOCATION ID
    # ========================================================

    if "Location_ID" not in locations.columns:

        locations["Location_ID"] = (

            locations["Ward_Name"]
            .astype(str)

            + "__"

            + locations["Point_ID"]
            .astype(str)

        )


    locations = (

        locations

        .drop_duplicates(
            subset=[
                "Location_ID"
            ]
        )

        .reset_index(
            drop=True
        )

    )


    if len(locations) != (
        EXPECTED_LOCATION_COUNT
    ):

        raise ValueError(

            f"Expected "
            f"{EXPECTED_LOCATION_COUNT} "
            f"locations but found "
            f"{len(locations)}."
        )


    print()

    print(
        f"Physical locations: "
        f"{len(locations)}"
    )

    print(
        f"Years: "
        f"{START_YEAR}–{END_YEAR}"
    )

    print(
        f"Batch size: "
        f"{BATCH_SIZE}"
    )

    print(
        f"Delay: "
        f"{REQUEST_DELAY_SECONDS} seconds"
    )


    # ========================================================
    # YEARS
    # ========================================================

    for year in range(

        START_YEAR,

        END_YEAR + 1

    ):

        print()

        print("=" * 70)

        print(
            f"YEAR {year}"
        )

        print("=" * 70)


        year_directory = (

            OUTPUT_ROOT

            / str(year)

        )


        year_directory.mkdir(

            parents=True,

            exist_ok=True

        )


        # ====================================================
        # MONTHS
        # ====================================================

        for (
            start_date,
            end_date,
            month_number
        ) in get_month_ranges(year):


            month_directory = (

                year_directory

                / month_number

            )


            month_directory.mkdir(

                parents=True,

                exist_ok=True

            )


            print()

            print(
                f"MONTH {year}-{month_number}"
            )


            # =================================================
            # BATCHES
            # =================================================

            number_of_batches = (

                (
                    len(locations)

                    + BATCH_SIZE

                    - 1

                )
                //
                BATCH_SIZE

            )


            for (
                batch_number,
                start
            ) in enumerate(

                range(

                    0,

                    len(locations),

                    BATCH_SIZE

                ),

                start=1

            ):


                batch = locations[
                    start:
                    start + BATCH_SIZE
                ]


                output_file = (

                    month_directory

                    / (

                        f"batch_"

                        f"{batch_number:03d}"

                        ".csv.gz"

                    )

                )


                expected_count = (

                    expected_rows(

                        start_date,

                        end_date,

                        len(batch)

                    )

                )


                # =============================================
                # RESUME
                # =============================================

                if is_valid_batch_file(

                    output_file,

                    expected_count

                ):

                    print(

                        f"⏭️ "

                        f"{output_file.name} "

                        f"already complete."

                    )

                    continue


                # =============================================
                # REMOVE INCOMPLETE FILE
                # =============================================

                if output_file.exists():

                    print(

                        f"⚠️ Removing incomplete "

                        f"{output_file.name}"

                    )

                    output_file.unlink()


                print()

                print(

                    f"Batch "

                    f"{batch_number}/"

                    f"{number_of_batches}"

                )

                print(

                    f"Locations: "

                    f"{len(batch)}"

                )

                print(

                    f"Expected rows: "

                    f"{expected_count:,}"

                )


                # =============================================
                # FETCH
                # =============================================

                responses = fetch_batch(

                    batch.to_dict(

                        orient="records"

                    ),

                    start_date,

                    end_date

                )


                # =============================================
                # CONVERT
                # =============================================

                frames = []


                for (

                    location,

                    response

                ) in zip(

                    batch.to_dict(

                        orient="records"

                    ),

                    responses

                ):


                    frame = (

                        response_to_dataframe(

                            location,

                            response

                        )

                    )


                    frames.append(
                        frame
                    )


                batch_data = pd.concat(

                    frames,

                    ignore_index=True

                )


                batch_data = (

                    batch_data

                    .sort_values(

                        [

                            "Location_ID",

                            "DateTime",

                        ]

                    )

                    .reset_index(
                        drop=True
                    )

                )


                # =============================================
                # VALIDATE
                # =============================================

                actual_count = len(
                    batch_data
                )


                if actual_count != (
                    expected_count
                ):

                    raise RuntimeError(

                        f"Row count mismatch: "

                        f"{actual_count:,} "

                        f"vs "

                        f"{expected_count:,}"

                    )


                # =============================================
                # SAVE
                # =============================================

                batch_data.to_csv(

                    output_file,

                    index=False,

                    compression="gzip"

                )


                print(

                    f"✅ Saved "

                    f"{actual_count:,} rows"

                )

                print(
                    output_file
                )


                # =============================================
                # DELAY
                # =============================================

                print(

                    f"Waiting "

                    f"{REQUEST_DELAY_SECONDS}s..."

                )


                time.sleep(

                    REQUEST_DELAY_SECONDS

                )


    print()

    print("=" * 70)

    print(
        "ALL HOURLY DATA DOWNLOAD COMPLETE"
    )

    print("=" * 70)


if __name__ == "__main__":

    main()