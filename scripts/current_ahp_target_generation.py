from pathlib import Path
import json
import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION
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

REPORT_DIR = (
    BASE_DIR
    / "data"
    / "current_ahp_target"
)

TARGET_DIR.mkdir(
    parents=True,
    exist_ok=True
)

REPORT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ------------------------------------------------------------
# Historical years
# ------------------------------------------------------------

YEARS = [
    2021,
    2022,
    2023,
    2024,
    2025,
]

TRAIN_YEARS = [
    2021,
    2022,
    2023,
]


# ------------------------------------------------------------
# TEST MODE
#
# IMPORTANT:
# Run only one month first.
#
# After we validate the target, change:
#
# TEST_MODE = False
#
# ------------------------------------------------------------

TEST_MODE = False

TEST_YEAR = 2025

TEST_MONTHS = [
    1,
    7,
]


# ------------------------------------------------------------
# Number of rows sampled per training month
# Used only to estimate robust normalization limits.
# ------------------------------------------------------------

SAMPLE_PER_MONTH = 10000

RANDOM_STATE = 42


# ============================================================
# AHP CRITERIA
# ============================================================

CRITERIA = [
    "Current_Rainfall_Pressure",
    "Antecedent_Wetness",
    "Drainage_Terrain_Susceptibility",
    "Urban_Runoff_Susceptibility",
    "Drying_Resistance",
]


# ============================================================
# AHP PAIRWISE COMPARISON MATRIX
# ============================================================

AHP_MATRIX = np.array([
    [1,    2,    3,    3,    4],
    [1/2,  1,    2,    2,    3],
    [1/3,  1/2,  1,    2,    2],
    [1/3,  1/2,  1/2,  1,    2],
    [1/4,  1/3,  1/2,  1/2,  1],
], dtype=float)


# ============================================================
# SAATY RANDOM INDEX
# ============================================================

RI_TABLE = {
    1: 0.00,
    2: 0.00,
    3: 0.58,
    4: 0.90,
    5: 1.12,
    6: 1.24,
    7: 1.32,
    8: 1.41,
    9: 1.45,
    10: 1.49,
}


# ============================================================
# CALCULATE AHP WEIGHTS
# ============================================================

def calculate_ahp_weights(matrix):

    eigenvalues, eigenvectors = np.linalg.eig(
        matrix
    )

    max_index = np.argmax(
        eigenvalues.real
    )

    lambda_max = float(
        eigenvalues[max_index].real
    )

    principal_vector = np.abs(
        eigenvectors[
            :,
            max_index
        ].real
    )

    weights = (
        principal_vector
        /
        principal_vector.sum()
    )

    n = matrix.shape[0]

    consistency_index = (
        lambda_max - n
    ) / (n - 1)

    random_index = RI_TABLE[n]

    consistency_ratio = (
        consistency_index
        /
        random_index
        if random_index > 0
        else 0.0
    )

    return (
        weights,
        lambda_max,
        consistency_index,
        consistency_ratio,
    )


# ============================================================
# MONTH FILES
# ============================================================

def month_files():

    files = []

    if TEST_MODE:

        years_months = [
            (TEST_YEAR, month)
            for month in TEST_MONTHS
        ]

    else:

        years_months = [
            (year, month)
            for year in YEARS
            for month in range(1, 13)
        ]

    for year, month in years_months:

        path = (
            FEATURE_DIR
            / str(year)
            / f"{month:02d}.parquet"
        )

        if not path.exists():

            raise FileNotFoundError(
                f"Missing feature file:\n{path}"
            )

        files.append(
            (
                year,
                month,
                path,
            )
        )

    return files


# ============================================================
# NORMALIZATION PARAMETERS
# ============================================================

NORMALIZATION_COLUMNS = [

    # Current rainfall
    "Rain_Last_1h",
    "Rain_Last_3h",
    "Max_Hourly_Rain_Last_6h",

    # Antecedent wetness
    "Rain_Last_24h",
    "Rain_Last_72h",

    # Drying
    "Relative_Humidity_pct",
    "Temperature_C",
    "Wind_Speed_kmh",
    "Shortwave_Radiation_W_m2",
    "Hours_Since_Last_Rain",
]


# ============================================================
# COLLECT TRAINING SAMPLES
# ============================================================

def collect_training_samples():

    print()
    print("=" * 70)
    print(
        "COLLECTING TRAINING-DATA "
        "NORMALIZATION SAMPLES"
    )
    print("=" * 70)

    samples = {
        column: []
        for column in NORMALIZATION_COLUMNS
    }

    for year in TRAIN_YEARS:

        for month in range(1, 13):

            current_path = (
                FEATURE_DIR
                / str(year)
                / f"{month:02d}.parquet"
            )

            if not current_path.exists():

                raise FileNotFoundError(
                    f"Missing feature file:\n"
                    f"{current_path}"
                )

            print(
                f"Sampling {year}-{month:02d} ..."
            )

            required_columns = [
                "Rain_Last_1h",
                "Rain_Last_3h",
                "Max_Hourly_Rain_Last_6h",
                "Rain_Last_24h",
                "Rain_Last_72h",
                "Relative_Humidity_pct",
                "Temperature_C",
                "Wind_Speed_kmh",
                "Shortwave_Radiation_W_m2",
                "Hours_Since_Last_Rain",
            ]

            df = pd.read_parquet(
                current_path,
                columns=required_columns,
            )

            if len(df) > SAMPLE_PER_MONTH:

                df = df.sample(
                    n=SAMPLE_PER_MONTH,
                    random_state=RANDOM_STATE,
                )

            for column in NORMALIZATION_COLUMNS:

                values = pd.to_numeric(
                    df[column],
                    errors="coerce",
                )

                if column == (
                    "Hours_Since_Last_Rain"
                ):

                    values = values.fillna(
                        168.0
                    )

                values = values.dropna()

                if len(values) > 0:

                    samples[
                        column
                    ].append(
                        values.to_numpy()
                    )

    parameters = {}

    for column in NORMALIZATION_COLUMNS:

        if not samples[column]:

            raise RuntimeError(
                f"No valid samples found "
                f"for {column}."
            )

        values = np.concatenate(
            samples[column]
        )

        low = float(
            np.percentile(
                values,
                1
            )
        )

        high = float(
            np.percentile(
                values,
                99
            )
        )

        if high <= low:

            raise ValueError(
                f"Invalid normalization range "
                f"for {column}: "
                f"{low} → {high}"
            )

        parameters[column] = {

            "p01":
                low,

            "p99":
                high,
        }

        print(
            f"{column:35s} "
            f"P01={low:.4f}  "
            f"P99={high:.4f}"
        )

    return parameters


# ============================================================
# NORMALIZE 0–1
# ============================================================

def normalize(
    values,
    low,
    high,
):

    result = (
        (values - low)
        /
        (high - low)
    )

    return np.clip(
        result,
        0,
        1,
    )


# ============================================================
# CREATE CURRENT-RISK CRITERIA
# ============================================================

def create_criteria(
    df,
    normalization,
):

    # ========================================================
    # CURRENT RAINFALL PRESSURE
    # ========================================================

    rain_1h = normalize(
        df["Rain_Last_1h"],
        normalization[
            "Rain_Last_1h"
        ]["p01"],
        normalization[
            "Rain_Last_1h"
        ]["p99"],
    )

    rain_3h = normalize(
        df["Rain_Last_3h"],
        normalization[
            "Rain_Last_3h"
        ]["p01"],
        normalization[
            "Rain_Last_3h"
        ]["p99"],
    )

    rain_peak_6h = normalize(
        df["Max_Hourly_Rain_Last_6h"],
        normalization[
            "Max_Hourly_Rain_Last_6h"
        ]["p01"],
        normalization[
            "Max_Hourly_Rain_Last_6h"
        ]["p99"],
    )

    # More emphasis on rainfall happening now.
    df["Criterion_Current_Rainfall"] = (
        0.50 * rain_1h
        + 0.30 * rain_3h
        + 0.20 * rain_peak_6h
    )


    # ========================================================
    # ANTECEDENT WETNESS
    # ========================================================

    rain_24 = normalize(
        df["Rain_Last_24h"],
        normalization[
            "Rain_Last_24h"
        ]["p01"],
        normalization[
            "Rain_Last_24h"
        ]["p99"],
    )

    rain_72 = normalize(
        df["Rain_Last_72h"],
        normalization[
            "Rain_Last_72h"
        ]["p01"],
        normalization[
            "Rain_Last_72h"
        ]["p99"],
    )

    df["Criterion_Antecedent_Wetness"] = (
        0.50 * rain_24
        + 0.50 * rain_72
    )


    # ========================================================
    # DRAINAGE / TERRAIN SUSCEPTIBILITY
    # ========================================================

    df["_flow"] = (
        df["Flow_Accumulation_km2"]
        .rank(pct=True)
    )

    df["_drain_distance"] = (
        df["Distance_to_Drain_m"]
        .rank(pct=True)
    )

    df["_drainage_density"] = (
        1
        -
        df[
            "Drainage_Density_km_per_km2"
        ].rank(pct=True)
    )

    df["_slope"] = (
        1
        -
        df["Slope_deg"]
        .rank(pct=True)
    )

    df[
        "Criterion_Drainage_Terrain"
    ] = (
        df[
            [
                "_flow",
                "_drain_distance",
                "_drainage_density",
                "_slope",
            ]
        ]
        .mean(axis=1)
    )


    # ========================================================
    # URBAN RUNOFF SUSCEPTIBILITY
    # ========================================================

    df["_builtup"] = (
        df["Builtup_Percent"]
        .rank(pct=True)
    )

    df["_road"] = (
        df[
            "Road_Density_km_per_km2"
        ]
        .rank(pct=True)
    )

    df["_vegetation"] = (
        1
        -
        df["Vegetation_Percent"]
        .rank(pct=True)
    )

    df[
        "Criterion_Urban_Runoff"
    ] = (
        df[
            [
                "_builtup",
                "_road",
                "_vegetation",
            ]
        ]
        .mean(axis=1)
    )


    # ========================================================
    # DRYING RESISTANCE
    # ========================================================

    humidity = normalize(
        df["Relative_Humidity_pct"],
        normalization[
            "Relative_Humidity_pct"
        ]["p01"],
        normalization[
            "Relative_Humidity_pct"
        ]["p99"],
    )

    temperature = (
        1
        -
        normalize(
            df["Temperature_C"],
            normalization[
                "Temperature_C"
            ]["p01"],
            normalization[
                "Temperature_C"
            ]["p99"],
        )
    )

    wind = (
        1
        -
        normalize(
            df["Wind_Speed_kmh"],
            normalization[
                "Wind_Speed_kmh"
            ]["p01"],
            normalization[
                "Wind_Speed_kmh"
            ]["p99"],
        )
    )

    solar = (
        1
        -
        normalize(
            df[
                "Shortwave_Radiation_W_m2"
            ],
            normalization[
                "Shortwave_Radiation_W_m2"
            ]["p01"],
            normalization[
                "Shortwave_Radiation_W_m2"
            ]["p99"],
        )
    )

    hours_since_raw = (
        df[
            "Hours_Since_Last_Rain"
        ]
        .fillna(168.0)
    )

    hours_since_log = np.log1p(
        hours_since_raw
    )

    h_low = np.log1p(
        normalization[
            "Hours_Since_Last_Rain"
        ]["p01"]
    )

    h_high = np.log1p(
        normalization[
            "Hours_Since_Last_Rain"
        ]["p99"]
    )

    hours_since_norm = normalize(
        hours_since_log,
        h_low,
        h_high,
    )

    hours_since_resistance = (
        1
        -
        hours_since_norm
    )

    df[
        "Criterion_Drying_Resistance"
    ] = (
        humidity
        + temperature
        + wind
        + solar
        + hours_since_resistance
    ) / 5.0


    # ========================================================
    # REMOVE TEMPORARY COLUMNS
    # ========================================================

    temporary = [
        "_flow",
        "_drain_distance",
        "_drainage_density",
        "_slope",
        "_builtup",
        "_road",
        "_vegetation",
    ]

    df.drop(
        columns=temporary,
        inplace=True,
        errors="ignore",
    )

    return df


# ============================================================
# CURRENT WATERLOGGING SCORE
# ============================================================

def calculate_current_score(
    df,
    weights,
):

    # ========================================================
    # WEATHER / MOISTURE PRESSURE
    # ========================================================
    #
    # These are direct indicators of water currently present
    # or recently accumulated.
    #
    # AHP weights:
    #   Current rainfall       ≈ 40%
    #   Antecedent wetness     ≈ 24%
    # ========================================================

    weather_contribution = (
        weights[0]
        * df[
            "Criterion_Current_Rainfall"
        ]

        +

        weights[1]
        * df[
            "Criterion_Antecedent_Wetness"
        ]
    )


    # ========================================================
    # LOCATION SUSCEPTIBILITY
    # ========================================================
    #
    # These describe how easily rainfall/wetness can produce
    # road waterlogging at this location.
    #
    # AHP weights:
    #   Drainage / terrain    ≈ 16%
    #   Urban runoff          ≈ 12%
    #   Drying resistance     ≈ 8%
    # ========================================================

    susceptibility_contribution = (
        weights[2]
        * df[
            "Criterion_Drainage_Terrain"
        ]

        +

        weights[3]
        * df[
            "Criterion_Urban_Runoff"
        ]

        +

        weights[4]
        * df[
            "Criterion_Drying_Resistance"
        ]
    )


    # ========================================================
    # MOISTURE ACTIVATION
    # ========================================================
    #
    # Use the stronger of:
    #
    #   1. current/recent rainfall pressure
    #   2. antecedent wetness
    #
    # This allows susceptibility to remain relevant after
    # rainfall temporarily stops, while completely dry
    # conditions produce zero waterlogging susceptibility.
    # ========================================================

    moisture_activation = np.maximum(
        df[
            "Criterion_Current_Rainfall"
        ],
        df[
            "Criterion_Antecedent_Wetness"
        ],
    )

    moisture_activation = np.clip(
        moisture_activation,
        0,
        1,
    )


    # ========================================================
    # FINAL CURRENT WATERLOGGING SCORE
    # ========================================================

    score = (
        weather_contribution

        +

        moisture_activation
        * susceptibility_contribution
    )

    score = (
        score
        * 100.0
    )


    return np.clip(
        score,
        0,
        100,
    )
# ============================================================
# CLASSIFICATION
# ============================================================

def assign_risk_level(
    score
):

    return pd.cut(
        score,
        bins=[
            -np.inf,
            30,
            60,
            90,
            np.inf,
        ],
        labels=[
            "LOW",
            "MODERATE",
            "HIGH",
            "EXTREME",
        ],
        right=False,
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "=" * 70
    )

    print(
        "CURRENT WATERLOGGING AHP "
        "TARGET CONSTRUCTION"
    )

    print(
        "=" * 70
    )

    if TEST_MODE:

        print()
        print(
            "⚠ TEST MODE ENABLED"
        )

        print(
            f"Processing only: "
            f"{TEST_YEAR}-"
            f"{TEST_MONTHS}"
        )

    # ========================================================
    # STEP 1 — AHP WEIGHTS
    # ========================================================

    (
        weights,
        lambda_max,
        consistency_index,
        consistency_ratio,
    ) = calculate_ahp_weights(
        AHP_MATRIX
    )

    print()
    print(
        "AHP RESULTS"
    )
    print(
        "-" * 70
    )

    for criterion, weight in zip(
        CRITERIA,
        weights,
    ):

        print(
            f"{criterion:40s}: "
            f"{weight:.6f} "
            f"({weight * 100:.2f}%)"
        )

    print(
        f"\nLambda max       : "
        f"{lambda_max:.6f}"
    )

    print(
        f"Consistency Index: "
        f"{consistency_index:.6f}"
    )

    print(
        f"Consistency Ratio: "
        f"{consistency_ratio:.6f}"
    )

    if consistency_ratio >= 0.10:

        raise RuntimeError(
            "AHP consistency ratio is "
            ">= 0.10."
        )

    print(
        "\n✅ AHP consistency acceptable "
        "(CR < 0.10)"
    )


    # ========================================================
    # STEP 2 — SAVE AHP MATRIX
    # ========================================================

    matrix_df = pd.DataFrame(
        AHP_MATRIX,
        index=CRITERIA,
        columns=CRITERIA,
    )

    matrix_df.to_csv(
        REPORT_DIR
        / "current_ahp_pairwise_matrix.csv"
    )

    weights_df = pd.DataFrame({

        "Criterion":
            CRITERIA,

        "AHP_Weight":
            weights,

        "Weight_Percent":
            weights * 100,
    })

    weights_df.to_csv(
        REPORT_DIR
        / "current_ahp_weights.csv",
        index=False,
    )


    # ========================================================
    # STEP 3 — NORMALIZATION
    # ========================================================

    normalization = (
        collect_training_samples()
    )

    with open(
        REPORT_DIR
        / "current_normalization_parameters.json",
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            normalization,
            f,
            indent=2,
        )


    # ========================================================
    # STEP 4 — PROCESS MONTHS
    # ========================================================

    summary_rows = []

    files = month_files()

    for file_index, (
        year,
        month,
        current_path,
    ) in enumerate(
        files,
        start=1
    ):

        print()
        print(
            "=" * 70
        )

        print(
            f"TARGET {file_index:02d}/"
            f"{len(files):02d} : "
            f"{year}-{month:02d}"
        )

        print(
            "=" * 70
        )

        columns = [

            "Location_ID",
            "DateTime",

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

            "Relative_Humidity_pct",
            "Temperature_C",
            "Wind_Speed_kmh",
            "Shortwave_Radiation_W_m2",

            "Flow_Accumulation_km2",
            "Slope_deg",
            "Distance_to_Drain_m",
            "Drainage_Density_km_per_km2",

            "Builtup_Percent",
            "Road_Density_km_per_km2",
            "Vegetation_Percent",
        ]

        df = pd.read_parquet(
            current_path,
            columns=columns,
        )

        # ----------------------------------------------------
        # TARGET VALIDITY
        #
        # No future rainfall is required.
        # We only require the historical wetness windows.
        # ----------------------------------------------------

        valid_antecedent = (
            df[
                [
                    "Rain_Last_24h",
                    "Rain_Last_72h",
                ]
            ]
            .notna()
            .all(axis=1)
        )

        valid_current = (
            df[
                [
                    "Rain_Last_1h",
                    "Rain_Last_3h",
                    "Max_Hourly_Rain_Last_6h",
                ]
            ]
            .notna()
            .all(axis=1)
        )

        df["Target_Valid"] = (
            valid_current
            &
            valid_antecedent
        )


        # ----------------------------------------------------
        # CRITERIA
        # ----------------------------------------------------

        df = create_criteria(
            df,
            normalization,
        )


        # ----------------------------------------------------
        # CURRENT RISK SCORE
        # ----------------------------------------------------

        df[
            "AHP_Waterlogging_Score"
        ] = calculate_current_score(
            df,
            weights,
        )


        # ----------------------------------------------------
        # CURRENT RISK LEVEL
        # ----------------------------------------------------

        df[
            "AHP_Waterlogging_Level"
        ] = assign_risk_level(
            df[
                "AHP_Waterlogging_Score"
            ]
        )


        # ----------------------------------------------------
        # OUTPUT
        # ----------------------------------------------------

        output = df[
            [

                "Location_ID",
                "DateTime",

                "Criterion_Current_Rainfall",

                "Criterion_Antecedent_Wetness",

                "Criterion_Drainage_Terrain",

                "Criterion_Urban_Runoff",

                "Criterion_Drying_Resistance",

                "AHP_Waterlogging_Score",

                "AHP_Waterlogging_Level",

                "Target_Valid",
            ]
        ].copy()


        # ----------------------------------------------------
        # SAVE
        # ----------------------------------------------------

        output_dir = (
            TARGET_DIR
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

        output.to_parquet(
            output_path,
            index=False,
            compression="snappy",
        )


        # ----------------------------------------------------
        # SUMMARY
        # ----------------------------------------------------

        valid_output = output[
            output["Target_Valid"]
        ].copy()

        counts = (
            valid_output[
                "AHP_Waterlogging_Level"
            ]
            .value_counts()
            .to_dict()
        )

        summary_rows.append({

            "Year":
                year,

            "Month":
                month,

            "Rows":
                len(output),

            "Valid_Target_Rows":
                len(valid_output),

            "Mean_AHP_Score":
                valid_output[
                    "AHP_Waterlogging_Score"
                ].mean(),

            "Min_AHP_Score":
                valid_output[
                    "AHP_Waterlogging_Score"
                ].min(),

            "Max_AHP_Score":
                valid_output[
                    "AHP_Waterlogging_Score"
                ].max(),

            "LOW":
                counts.get(
                    "LOW",
                    0,
                ),

            "MODERATE":
                counts.get(
                    "MODERATE",
                    0,
                ),

            "HIGH":
                counts.get(
                    "HIGH",
                    0,
                ),

            "EXTREME":
                counts.get(
                    "EXTREME",
                    0,
                ),
        })


        print(
            f"✅ Saved: {output_path}"
        )

        print(
            f"Rows: "
            f"{len(output):,}"
        )

        print(
            f"Valid target rows: "
            f"{len(valid_output):,}"
        )

        print(
            f"Mean score: "
            f"{valid_output['AHP_Waterlogging_Score'].mean():.2f}"
        )


    # ========================================================
    # SAVE SUMMARY
    # ========================================================

    summary_df = pd.DataFrame(
        summary_rows
    )

    summary_df.to_csv(
        REPORT_DIR
        / "current_target_generation_summary.csv",
        index=False,
    )


    print()
    print(
        "=" * 70
    )

    if TEST_MODE:

        print(
            "✅ CURRENT-RISK AHP TEST COMPLETE"
        )

        print()
        print(
            "TEST MODE IS STILL ENABLED."
        )

        print(
            "Review the July 2025 target before "
            "generating all 60 months."
        )

    else:

        print(
            "✅ CURRENT-RISK AHP TARGET "
            "GENERATION COMPLETE"
        )

    print(
        "=" * 70
    )

    print()
    print(
        f"Target directory:\n{TARGET_DIR}"
    )

    print()
    print(
        f"Report directory:\n{REPORT_DIR}"
    )


if __name__ == "__main__":
    main()