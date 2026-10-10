from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

FEATURE_DIR = (
    BASE_DIR
    / "data"
    / "hourly_features"
)

TARGET_DIR = (
    BASE_DIR
    / "data"
    / "current_hourly_targets"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "current_ml_ready"
)

REPORT_DIR = (
    BASE_DIR
    / "data"
    / "current_ml_ready_reports"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

REPORT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# YEARS
# ============================================================

YEARS = [
    2021,
    2022,
    2023,
    2024,
    2025,
]


# ============================================================
# FINAL 34 ML FEATURES
#
# EXACT SAME ORDER USED BY THE CURRENT HGB DESIGN
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
# TARGET COLUMNS
# ============================================================

TARGET_COLUMNS = [
    "AHP_Waterlogging_Score",
    "AHP_Waterlogging_Level",
    "Target_Valid",
]


# ============================================================
# IDENTIFIER COLUMNS
# ============================================================

IDENTIFIER_COLUMNS = [
    "Location_ID",
    "DateTime",
]


# ============================================================
# DATETIME NORMALIZATION
# ============================================================

def normalize_datetime(df):

    df["DateTime"] = pd.to_datetime(
        df["DateTime"],
        errors="coerce",
    )

    if df["DateTime"].dt.tz is not None:

        df["DateTime"] = (
            df["DateTime"]
            .dt
            .tz_localize(None)
        )

    return df


# ============================================================
# PROCESS ONE MONTH
# ============================================================

def process_month(
    year,
    month,
):

    feature_path = (
        FEATURE_DIR
        / str(year)
        / f"{month:02d}.parquet"
    )

    target_path = (
        TARGET_DIR
        / str(year)
        / f"{month:02d}.parquet"
    )

    output_dir = (
        OUTPUT_DIR
        / str(year)
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        output_dir
        / f"{month:02d}.parquet"
    )


    # ========================================================
    # CHECK FILES
    # ========================================================

    if not feature_path.exists():

        raise FileNotFoundError(
            f"Missing feature file:\n"
            f"{feature_path}"
        )

    if not target_path.exists():

        raise FileNotFoundError(
            f"Missing current-risk target file:\n"
            f"{target_path}"
        )


    # ========================================================
    # READ FEATURES
    # ========================================================

    feature_columns = (
        IDENTIFIER_COLUMNS
        + MODEL_FEATURES
    )

    print(
        f"  Reading features: "
        f"{feature_path.name}"
    )

    features = pd.read_parquet(
        feature_path,
        columns=feature_columns,
    )

    features = normalize_datetime(
        features
    )


    # ========================================================
    # READ CURRENT-RISK TARGET
    # ========================================================

    target_columns = (
        IDENTIFIER_COLUMNS
        + TARGET_COLUMNS
    )

    print(
        f"  Reading targets : "
        f"{target_path.name}"
    )

    targets = pd.read_parquet(
        target_path,
        columns=target_columns,
    )

    targets = normalize_datetime(
        targets
    )


    # ========================================================
    # CHECK DUPLICATES
    # ========================================================

    feature_duplicates = (
        features
        .duplicated(
            subset=IDENTIFIER_COLUMNS
        )
        .sum()
    )

    if feature_duplicates > 0:

        raise ValueError(
            f"{year}-{month:02d}: "
            f"{feature_duplicates:,} duplicate "
            f"feature keys found."
        )


    target_duplicates = (
        targets
        .duplicated(
            subset=IDENTIFIER_COLUMNS
        )
        .sum()
    )

    if target_duplicates > 0:

        raise ValueError(
            f"{year}-{month:02d}: "
            f"{target_duplicates:,} duplicate "
            f"target keys found."
        )


    # ========================================================
    # MERGE
    # ========================================================

    print(
        "  Joining features + current-risk target..."
    )

    merged = features.merge(
        targets,
        on=IDENTIFIER_COLUMNS,
        how="inner",
        validate="one_to_one",
    )

    print(
        f"  Joined rows: "
        f"{len(merged):,}"
    )


    # ========================================================
    # CHECK ROW COUNTS
    # ========================================================

    if len(merged) != len(features):

        missing_feature_matches = (
            len(features)
            -
            len(merged)
        )

        raise ValueError(
            f"{year}-{month:02d}: "
            f"{missing_feature_matches:,} "
            f"feature rows did not match "
            f"a target row."
        )


    if len(merged) != len(targets):

        missing_target_matches = (
            len(targets)
            -
            len(merged)
        )

        raise ValueError(
            f"{year}-{month:02d}: "
            f"{missing_target_matches:,} "
            f"target rows did not match "
            f"a feature row."
        )


    # ========================================================
    # KEEP ONLY VALID SUPERVISED TARGET ROWS
    # ========================================================

    valid_mask = (
        merged["Target_Valid"]
        .astype(bool)
    )

    valid_rows = int(
        valid_mask.sum()
    )

    invalid_rows = (
        len(merged)
        -
        valid_rows
    )

    print(
        f"  Valid target rows: "
        f"{valid_rows:,}"
    )

    print(
        f"  Invalid target rows: "
        f"{invalid_rows:,}"
    )

    ml = (
        merged[
            valid_mask
        ]
        .copy()
    )


    # ========================================================
    # NUMERIC FEATURE CONVERSION
    # ========================================================

    for column in MODEL_FEATURES:

        ml[column] = pd.to_numeric(
            ml[column],
            errors="coerce",
        )


    # ========================================================
    # TARGET NUMERIC CONVERSION
    # ========================================================

    ml[
        "AHP_Waterlogging_Score"
    ] = pd.to_numeric(
        ml[
            "AHP_Waterlogging_Score"
        ],
        errors="coerce",
    )

    # ========================================================
    # REMOVE ROWS WITH INCOMPLETE ML FEATURES
    # ========================================================
    #
    # The current-risk target becomes valid after the required
    # rainfall history is available, but the ML model also needs
    # the full 34-feature vector.
    #
    # In particular, Rain_Last_168h requires a complete 168-hour
    # historical window. At the beginning of the 2021 archive,
    # those rows are intentionally excluded rather than fabricated.
    # ========================================================

    feature_complete_mask = (
        ml[
            MODEL_FEATURES
        ]
        .notna()
        .all(axis=1)
    )

    incomplete_feature_rows = int(
        (~feature_complete_mask).sum()
    )

    if incomplete_feature_rows > 0:
        print(
            f"  Removing incomplete ML rows: "
            f"{incomplete_feature_rows:,}"
        )

        missing_counts = (
            ml.loc[
                ~feature_complete_mask,
                MODEL_FEATURES
            ]
            .isna()
            .sum()
        )

        bad_missing = (
            missing_counts[
                missing_counts > 0
                ]
        )

        print(
            "  Missing-feature breakdown:"
        )

        print(
            bad_missing.to_string()
        )

        ml = ml[
            feature_complete_mask
        ].copy()


    # ========================================================
    # CHECK MISSING TARGET
    # ========================================================

    missing_target = int(
        ml[
            "AHP_Waterlogging_Score"
        ]
        .isna()
        .sum()
    )

    if missing_target > 0:

        raise ValueError(
            f"{year}-{month:02d}: "
            f"{missing_target:,} missing target values."
        )


    # ========================================================
    # CHECK TARGET RANGE
    # ========================================================

    target_min = float(
        ml[
            "AHP_Waterlogging_Score"
        ].min()
    )

    target_max = float(
        ml[
            "AHP_Waterlogging_Score"
        ].max()
    )

    if target_min < 0:

        raise ValueError(
            f"{year}-{month:02d}: "
            f"Negative target detected: "
            f"{target_min}"
        )

    if target_max > 100:

        raise ValueError(
            f"{year}-{month:02d}: "
            f"Target above 100 detected: "
            f"{target_max}"
        )


    # ========================================================
    # CHECK FEATURE COUNT
    # ========================================================

    actual_feature_count = len(
        MODEL_FEATURES
    )

    if actual_feature_count != 34:

        raise RuntimeError(
            f"Expected 34 model features, "
            f"found {actual_feature_count}."
        )


    # ========================================================
    # EXPLICITLY PREVENT FUTURE FEATURES
    # ========================================================

    forbidden_future_features = [

        "Rain_Next_1h",
        "Rain_Next_2h",
        "Rain_Next_3h",
        "Rain_Next_3h_Total",
        "Max_Rain_Next_3h",

        "Forecast_Rain_Next_1h",
        "Forecast_Rain_Next_2h",
        "Forecast_Rain_Next_3h",
        "Forecast_Rain_3h_Total",
        "Forecast_Max_Rain_Next_3h",
    ]

    found_forbidden = [
        column
        for column in forbidden_future_features
        if column in ml.columns
    ]

    if found_forbidden:

        raise RuntimeError(
            f"Future/forecast columns detected "
            f"in ML-ready data:\n"
            f"{found_forbidden}"
        )


    # ========================================================
    # FINAL COLUMN ORDER
    # ========================================================

    final_columns = (
        IDENTIFIER_COLUMNS
        +
        MODEL_FEATURES
        +
        TARGET_COLUMNS
    )

    ml = ml[
        final_columns
    ].copy()


    # ========================================================
    # SAVE
    # ========================================================

    ml.to_parquet(
        output_path,
        index=False,
        compression="snappy",
    )


    # ========================================================
    # MONTH SUMMARY
    # ========================================================

    level_counts = (
        ml[
            "AHP_Waterlogging_Level"
        ]
        .value_counts()
        .to_dict()
    )

    summary = {

        "Year":
            year,

        "Month":
            month,

        "Input_Feature_Rows":
            len(features),

        "Input_Target_Rows":
            len(targets),

        "Valid_ML_Rows":
            len(ml),

        "Invalid_Target_Rows":
            invalid_rows,

        "Invalid_ML_Feature_Rows":
            incomplete_feature_rows,

        "Feature_Count":
            len(MODEL_FEATURES),

        "Mean_Target":
            float(
                ml[
                    "AHP_Waterlogging_Score"
                ].mean()
            ),

        "Min_Target":
            target_min,

        "Max_Target":
            target_max,

        "LOW":
            int(
                level_counts.get(
                    "LOW",
                    0,
                )
            ),

        "MODERATE":
            int(
                level_counts.get(
                    "MODERATE",
                    0,
                )
            ),

        "HIGH":
            int(
                level_counts.get(
                    "HIGH",
                    0,
                )
            ),

        "EXTREME":
            int(
                level_counts.get(
                    "EXTREME",
                    0,
                )
            ),
    }

    print(
        f"  ✅ Saved: {output_path}"
    )

    return summary


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "=" * 80
    )

    print(
        "CURRENT-RISK ML-READY DATASET CREATION"
    )

    print(
        "=" * 80
    )

    print()
    print(
        "Model feature count:"
        f" {len(MODEL_FEATURES)}"
    )

    print()
    print(
        "IMPORTANT:"
    )

    print(
        "This dataset uses ONLY current/past "
        "information as model inputs."
    )

    print(
        "No future rainfall or forecast columns "
        "are used."
    )

    summary_rows = []

    total_input_rows = 0
    total_valid_rows = 0
    total_invalid_rows = 0

    for year in YEARS:

        print()
        print(
            "=" * 80
        )

        print(
            f"YEAR {year}"
        )

        print(
            "=" * 80
        )

        for month in range(1, 13):

            print()
            print(
                f"MONTH {year}-{month:02d}"
            )

            summary = process_month(
                year,
                month,
            )

            summary_rows.append(
                summary
            )

            total_input_rows += (
                summary[
                    "Input_Feature_Rows"
                ]
            )

            total_valid_rows += (
                summary[
                    "Valid_ML_Rows"
                ]
            )

            total_invalid_rows += (
                summary[
                    "Invalid_Target_Rows"
                ]
            )


    # ========================================================
    # SAVE SUMMARY
    # ========================================================

    summary_df = pd.DataFrame(
        summary_rows
    )

    summary_path = (
        REPORT_DIR
        / "current_ml_ready_generation_summary.csv"
    )

    summary_df.to_csv(
        summary_path,
        index=False,
    )


    # ========================================================
    # GLOBAL SUMMARY
    # ========================================================

    print()
    print(
        "=" * 80
    )

    print(
        "CURRENT-RISK ML-READY DATASET COMPLETE"
    )

    print(
        "=" * 80
    )

    print()
    print(
        f"Total input rows : "
        f"{total_input_rows:,}"
    )

    print(
        f"Valid ML rows    : "
        f"{total_valid_rows:,}"
    )

    print(
        f"Invalid rows     : "
        f"{total_invalid_rows:,}"
    )

    print()
    print(
        f"Output directory:"
    )

    print(
        OUTPUT_DIR
    )

    print()
    print(
        f"Summary:"
    )

    print(
        summary_path
    )

    print()
    print(
        "✅ Current-risk ML-ready dataset "
        "generation completed."
    )


if __name__ == "__main__":
    main()