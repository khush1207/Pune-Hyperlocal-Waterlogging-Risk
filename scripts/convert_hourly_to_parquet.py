from pathlib import Path
import calendar
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent

RAW_ROOT = (
    PROJECT_ROOT
    / "data"
    / "hourly_raw_historical_forecast"
)

PARQUET_ROOT = (
    PROJECT_ROOT
    / "data"
    / "hourly_parquet"
)

START_YEAR = 2021
END_YEAR = 2025


# ============================================================
# COLUMN NORMALIZATION
# ============================================================

def normalize_columns(df):

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

    # Keep only the standardized weather columns
    required_columns = [
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
        for col in required_columns
        if col not in df.columns
    ]

    if missing:
        raise RuntimeError(
            f"Missing columns after normalization: {missing}"
        )

    return df[required_columns]


# ============================================================
# DATETIME NORMALIZATION
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
# CONVERT ONE MONTH
# ============================================================

def convert_month(year, month):

    month_dir = (
        RAW_ROOT
        / str(year)
        / f"{month:02d}"
    )

    output_dir = (
        PARQUET_ROOT
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

    if output_file.exists():

        print(
            f"✅ Already exists: "
            f"{output_file}"
        )

        return

    files = sorted(
        month_dir.glob(
            "batch_*.csv.gz"
        )
    )

    if not files:

        raise RuntimeError(
            f"No batch files found for "
            f"{year}-{month:02d}"
        )

    print()
    print("=" * 70)
    print(
        f"CONVERTING {year}-{month:02d}"
    )
    print("=" * 70)

    frames = []

    for i, file_path in enumerate(
        files,
        start=1,
    ):

        print(
            f"Reading batch "
            f"{i}/{len(files)}: "
            f"{file_path.name}"
        )

        df = pd.read_csv(
            file_path,
            compression="gzip",
        )

        df = normalize_columns(
            df
        )

        df["DateTime"] = normalize_datetime(
            df["DateTime"]
        )

        # Numeric normalization
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
            .clip(lower=0)
        )

        frames.append(
            df
        )

    # --------------------------------------------------------
    # COMBINE MONTH
    # --------------------------------------------------------

    month_df = pd.concat(
        frames,
        ignore_index=True,
    )

    # --------------------------------------------------------
    # SORT
    # --------------------------------------------------------

    month_df = month_df.sort_values(
        [
            "Location_ID",
            "DateTime",
        ]
    ).reset_index(
        drop=True
    )

    # --------------------------------------------------------
    # BASIC VALIDATION
    # --------------------------------------------------------

    expected_days = calendar.monthrange(
        year,
        month,
    )[1]

    expected_rows = (
        482
        * expected_days
        * 24
    )

    actual_rows = len(
        month_df
    )

    if actual_rows != expected_rows:

        raise RuntimeError(
            f"{year}-{month:02d}: "
            f"expected {expected_rows:,} "
            f"rows but found "
            f"{actual_rows:,}"
        )

    unique_locations = (
        month_df["Location_ID"]
        .nunique()
    )

    if unique_locations != 482:

        raise RuntimeError(
            f"{year}-{month:02d}: "
            f"expected 482 locations but "
            f"found {unique_locations}"
        )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    month_df.to_parquet(
        output_file,
        engine="pyarrow",
        index=False,
        compression="snappy",
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
        f"{actual_rows:,}"
    )

    print(
        f"Locations: "
        f"{unique_locations}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("CSV.GZ → PARQUET CONVERSION")
    print("=" * 70)

    for year in range(
        START_YEAR,
        END_YEAR + 1,
    ):

        for month in range(
            1,
            13,
        ):

            convert_month(
                year,
                month,
            )

    print()
    print("=" * 70)
    print("✅ PARQUET CONVERSION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()