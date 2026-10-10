from pathlib import Path
import json

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    confusion_matrix,
    precision_recall_fscore_support,
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

ML_DIR = (
    BASE_DIR
    / "data"
    / "current_ml_ready"
)

MODEL_DIR = (
    BASE_DIR
    / "models"
)

MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# DATA SPLIT
# ============================================================

TRAIN_YEARS = [
    2021,
    2022,
    2023,
]

VALIDATION_YEAR = 2024


# ============================================================
# SAMPLING
# ============================================================

# Same approach as the previous project model:
# 50,000 rows per month.
SAMPLE_PER_MONTH = 50_000

RANDOM_STATE = 42


# ============================================================
# MODEL FEATURES
# EXACT 34 FEATURES
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
# TARGET
# ============================================================

TARGET_COLUMN = (
    "AHP_Waterlogging_Score"
)

LEVEL_COLUMN = (
    "AHP_Waterlogging_Level"
)


# ============================================================
# RISK WEIGHTS
# ============================================================

RISK_WEIGHTS = {

    "LOW":
        1.0,

    "MODERATE":
        1.5,

    "HIGH":
        5.0,

    "EXTREME":
        15.0,
}


# ============================================================
# RISK CLASSIFICATION
# ============================================================

def classify_risk(score):

    score = float(score)

    if score < 30:
        return "LOW"

    if score < 60:
        return "MODERATE"

    if score < 90:
        return "HIGH"

    return "EXTREME"


# ============================================================
# LOAD TRAINING DATA
# ============================================================

def load_training_sample():

    X_parts = []
    y_parts = []
    w_parts = []

    total_rows_seen = 0
    total_rows_sampled = 0

    print()
    print("=" * 80)
    print("LOADING CURRENT-RISK TRAINING DATA")
    print("=" * 80)

    for year in TRAIN_YEARS:

        print()
        print(f"YEAR {year}")
        print("-" * 80)

        for month in range(1, 13):

            path = (
                ML_DIR
                / str(year)
                / f"{month:02d}.parquet"
            )

            if not path.exists():

                raise FileNotFoundError(
                    f"Missing ML-ready file:\n"
                    f"{path}"
                )

            df = pd.read_parquet(
                path,
                columns=(
                    MODEL_FEATURES
                    + [
                        TARGET_COLUMN,
                        LEVEL_COLUMN,
                    ]
                ),
            )

            rows = len(df)

            total_rows_seen += rows

            # ------------------------------------------------
            # Deterministic monthly sample
            # ------------------------------------------------

            if rows > SAMPLE_PER_MONTH:

                seed = (
                    RANDOM_STATE
                    + year * 100
                    + month
                )

                df = df.sample(
                    n=SAMPLE_PER_MONTH,
                    random_state=seed,
                )

            sampled = len(df)

            total_rows_sampled += sampled

            print(
                f"{year}-{month:02d}: "
                f"{rows:,} rows → "
                f"{sampled:,} sampled"
            )

            # ------------------------------------------------
            # Convert features
            # ------------------------------------------------

            X = (
                df[
                    MODEL_FEATURES
                ]
                .to_numpy(
                    dtype=np.float32
                )
            )

            y = (
                pd.to_numeric(
                    df[
                        TARGET_COLUMN
                    ],
                    errors="coerce",
                )
                .to_numpy(
                    dtype=np.float32
                )
            )

            levels = (
                df[
                    LEVEL_COLUMN
                ]
                .astype(str)
                .to_numpy()
            )

            # ------------------------------------------------
            # Check
            # ------------------------------------------------

            if not np.isfinite(X).all():

                raise ValueError(
                    f"Invalid feature value in "
                    f"{year}-{month:02d}"
                )

            if not np.isfinite(y).all():

                raise ValueError(
                    f"Invalid target value in "
                    f"{year}-{month:02d}"
                )

            # ------------------------------------------------
            # Sample weights
            # ------------------------------------------------

            sample_weights = np.array(
                [
                    RISK_WEIGHTS.get(
                        level,
                        1.0,
                    )
                    for level in levels
                ],
                dtype=np.float32,
            )

            X_parts.append(X)
            y_parts.append(y)
            w_parts.append(sample_weights)

    # --------------------------------------------------------
    # Combine
    # --------------------------------------------------------

    X_train = np.concatenate(
        X_parts,
        axis=0,
    )

    y_train = np.concatenate(
        y_parts,
        axis=0,
    )

    sample_weights = np.concatenate(
        w_parts,
        axis=0,
    )

    print()
    print("=" * 80)
    print("TRAINING DATA READY")
    print("=" * 80)

    print(
        f"Rows seen    : "
        f"{total_rows_seen:,}"
    )

    print(
        f"Rows sampled : "
        f"{total_rows_sampled:,}"
    )

    print(
        f"Features     : "
        f"{X_train.shape[1]}"
    )

    print(
        f"X shape      : "
        f"{X_train.shape}"
    )

    print(
        f"y shape      : "
        f"{y_train.shape}"
    )

    return (
        X_train,
        y_train,
        sample_weights,
    )


# ============================================================
# TRAIN MODEL
# ============================================================

def train_model(
    X_train,
    y_train,
    sample_weights,
):

    print()
    print("=" * 80)
    print("TRAINING CURRENT-RISK HGB")
    print("=" * 80)

    model = HistGradientBoostingRegressor(

        learning_rate=0.08,

        max_iter=150,

        max_leaf_nodes=31,

        min_samples_leaf=100,

        l2_regularization=1.0,

        max_bins=127,

        early_stopping=False,

        random_state=42,
    )

    print()
    print("Model configuration:")
    print(
        "  learning_rate     = 0.08"
    )
    print(
        "  max_iter          = 150"
    )
    print(
        "  max_leaf_nodes    = 31"
    )
    print(
        "  min_samples_leaf  = 100"
    )
    print(
        "  l2_regularization = 1.0"
    )
    print(
        "  max_bins          = 127"
    )
    print(
        "  early_stopping    = False"
    )

    print()
    print(
        "Fitting model..."
    )

    model.fit(
        X_train,
        y_train,
        sample_weight=sample_weights,
    )

    print()
    print(
        "✅ Model training complete."
    )

    return model


# ============================================================
# VALIDATION
# ============================================================

def evaluate_validation(
    model
):

    print()
    print("=" * 80)
    print("VALIDATING ON 2024")
    print("=" * 80)

    total_rows = 0

    absolute_error_sum = 0.0
    squared_error_sum = 0.0

    y_sum = 0.0
    y_squared_sum = 0.0

    confusion = np.zeros(
        (4, 4),
        dtype=np.int64,
    )

    levels = [
        "LOW",
        "MODERATE",
        "HIGH",
        "EXTREME",
    ]

    level_to_index = {
        level: index
        for index, level
        in enumerate(levels)
    }

    for month in range(1, 13):

        path = (
            ML_DIR
            / str(VALIDATION_YEAR)
            / f"{month:02d}.parquet"
        )

        if not path.exists():

            raise FileNotFoundError(
                f"Missing validation file:\n"
                f"{path}"
            )

        df = pd.read_parquet(
            path,
            columns=(
                MODEL_FEATURES
                + [
                    TARGET_COLUMN,
                ]
            ),
        )

        X = (
            df[
                MODEL_FEATURES
            ]
            .to_numpy(
                dtype=np.float32
            )
        )

        y = (
            pd.to_numeric(
                df[
                    TARGET_COLUMN
                ],
                errors="coerce",
            )
            .to_numpy(
                dtype=np.float64
            )
        )

        if not np.isfinite(X).all():

            raise ValueError(
                f"Invalid validation "
                f"features in 2024-{month:02d}"
            )

        if not np.isfinite(y).all():

            raise ValueError(
                f"Invalid validation "
                f"target in 2024-{month:02d}"
            )

        predictions = model.predict(
            X
        )

        predictions = np.clip(
            predictions,
            0,
            100,
        )

        # ----------------------------------------------------
        # Regression statistics
        # ----------------------------------------------------

        errors = (
            predictions
            -
            y
        )

        absolute_error_sum += float(
            np.abs(errors).sum()
        )

        squared_error_sum += float(
            np.square(errors).sum()
        )

        y_sum += float(
            y.sum()
        )

        y_squared_sum += float(
            np.square(y).sum()
        )

        total_rows += len(y)

        # ----------------------------------------------------
        # Classification confusion matrix
        # ----------------------------------------------------

        actual_classes = [
            level_to_index[
                classify_risk(value)
            ]
            for value in y
        ]

        predicted_classes = [
            level_to_index[
                classify_risk(value)
            ]
            for value in predictions
        ]

        month_cm = confusion_matrix(
            actual_classes,
            predicted_classes,
            labels=[
                0,
                1,
                2,
                3,
            ],
        )

        confusion += month_cm

        print(
            f"2024-{month:02d}: "
            f"{len(y):,} rows evaluated"
        )

    # ========================================================
    # FINAL REGRESSION METRICS
    # ========================================================

    mae = (
        absolute_error_sum
        /
        total_rows
    )

    rmse = np.sqrt(
        squared_error_sum
        /
        total_rows
    )

    y_mean = (
        y_sum
        /
        total_rows
    )

    total_variation = (
        y_squared_sum
        -
        total_rows
        * y_mean ** 2
    )

    residual_variation = (
        squared_error_sum
    )

    r2 = (
        1.0
        -
        residual_variation
        /
        total_variation
        if total_variation > 0
        else np.nan
    )

    # ========================================================
    # CLASSIFICATION METRICS
    # ========================================================

    true_counts = (
        confusion.sum(axis=1)
    )

    predicted_counts = (
        confusion.sum(axis=0)
    )

    recalls = np.zeros(
        4,
        dtype=float,
    )

    precisions = np.zeros(
        4,
        dtype=float,
    )

    f1_values = np.zeros(
        4,
        dtype=float,
    )

    for index in range(4):

        tp = confusion[
            index,
            index
        ]

        actual = true_counts[
            index
        ]

        predicted = predicted_counts[
            index
        ]

        if actual > 0:
            recalls[index] = (
                tp / actual
            )

        if predicted > 0:
            precisions[index] = (
                tp / predicted
            )

        if (
            precisions[index]
            +
            recalls[index]
            > 0
        ):
            f1_values[index] = (
                2
                * precisions[index]
                * recalls[index]
                /
                (
                    precisions[index]
                    +
                    recalls[index]
                )
            )

    accuracy = (
        np.trace(confusion)
        /
        total_rows
    )

    balanced_accuracy = (
        recalls.mean()
    )

    macro_f1 = (
        f1_values.mean()
    )

    tail_actual = (
        true_counts[2]
        +
        true_counts[3]
    )

    tail_true_positive = (
        confusion[2, 2]
        +
        confusion[2, 3]
        +
        confusion[3, 2]
        +
        confusion[3, 3]
    )

    tail_predicted = (
        predicted_counts[2]
        +
        predicted_counts[3]
    )

    tail_precision = (
        tail_true_positive
        /
        tail_predicted
        if tail_predicted > 0
        else 0.0
    )

    tail_recall = (
        tail_true_positive
        /
        tail_actual
        if tail_actual > 0
        else 0.0
    )

    tail_f1 = (
        2
        * tail_precision
        * tail_recall
        /
        (
            tail_precision
            +
            tail_recall
        )
        if (
            tail_precision
            +
            tail_recall
            > 0
        )
        else 0.0
    )

    # ========================================================
    # PRINT RESULTS
    # ========================================================

    print()
    print("=" * 80)
    print("2024 VALIDATION RESULTS")
    print("=" * 80)

    print()
    print(
        f"Rows                 : "
        f"{total_rows:,}"
    )

    print(
        f"MAE                  : "
        f"{mae:.4f}"
    )

    print(
        f"RMSE                 : "
        f"{rmse:.4f}"
    )

    print(
        f"R²                   : "
        f"{r2:.4f}"
    )

    print(
        f"Accuracy             : "
        f"{accuracy:.4f}"
    )

    print(
        f"Balanced Accuracy    : "
        f"{balanced_accuracy:.4f}"
    )

    print(
        f"Macro F1             : "
        f"{macro_f1:.4f}"
    )

    print(
        f"Tail F1 (HIGH+EXTREME): "
        f"{tail_f1:.4f}"
    )

    print()
    print(
        "PER-LEVEL METRICS"
    )
    print("-" * 80)

    for index, level in enumerate(
        levels
    ):

        print(
            f"{level:10s} | "
            f"Precision={precisions[index]:.4f} | "
            f"Recall={recalls[index]:.4f} | "
            f"F1={f1_values[index]:.4f} | "
            f"Actual={true_counts[index]:,}"
        )

    print()
    print(
        "CONFUSION MATRIX"
    )

    cm_df = pd.DataFrame(
        confusion,
        index=[
            f"Actual_{x}"
            for x in levels
        ],
        columns=[
            f"Pred_{x}"
            for x in levels
        ],
    )

    print(
        cm_df.to_string()
    )

    return {

        "validation_year":
            VALIDATION_YEAR,

        "rows":
            int(total_rows),

        "MAE":
            float(mae),

        "RMSE":
            float(rmse),

        "R2":
            float(r2),

        "Accuracy":
            float(accuracy),

        "Balanced_Accuracy":
            float(
                balanced_accuracy
            ),

        "Macro_F1":
            float(
                macro_f1
            ),

        "Tail_F1":
            float(
                tail_f1
            ),

        "LOW_Recall":
            float(
                recalls[0]
            ),

        "MODERATE_Recall":
            float(
                recalls[1]
            ),

        "HIGH_Recall":
            float(
                recalls[2]
            ),

        "EXTREME_Recall":
            float(
                recalls[3]
            ),

        "LOW_F1":
            float(
                f1_values[0]
            ),

        "MODERATE_F1":
            float(
                f1_values[1]
            ),

        "HIGH_F1":
            float(
                f1_values[2]
            ),

        "EXTREME_F1":
            float(
                f1_values[3]
            ),

        "confusion_matrix":
            confusion.tolist(),
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 80)
    print("CURRENT-RISK HGB — TRAIN + 2024 VALIDATION")
    print("=" * 80)

    print()
    print(
        "IMPORTANT:"
    )

    print(
        "2025 is NOT used at this stage."
    )

    print(
        "The existing baseline model is NOT overwritten."
    )

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    (
        X_train,
        y_train,
        sample_weights,
    ) = load_training_sample()

    # --------------------------------------------------------
    # Train
    # --------------------------------------------------------

    model = train_model(
        X_train,
        y_train,
        sample_weights,
    )

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    validation_results = (
        evaluate_validation(
            model
        )
    )

    # --------------------------------------------------------
    # Save model
    # --------------------------------------------------------

    model_path = (
        MODEL_DIR
        / "current_hourly_waterlogging_hgb_validation.joblib"
    )

    joblib.dump(
        model,
        model_path,
    )

    print()
    print(
        f"✅ Validation model saved:"
    )

    print(
        model_path
    )

    # --------------------------------------------------------
    # Metadata
    # --------------------------------------------------------

    metadata = {

        "model_type":
            "HistGradientBoostingRegressor",

        "prediction_target":
            TARGET_COLUMN,

        "risk_type":
            "CURRENT_ROAD_WATERLOGGING_RISK",

        "model_features":
            MODEL_FEATURES,

        "feature_count":
            len(MODEL_FEATURES),

        "training_years":
            TRAIN_YEARS,

        "validation_year":
            VALIDATION_YEAR,

        "sample_per_month":
            SAMPLE_PER_MONTH,

        "risk_weights":
            RISK_WEIGHTS,

        "risk_thresholds": {
            "LOW":
                "<30",

            "MODERATE":
                "30-<60",

            "HIGH":
                "60-<90",

            "EXTREME":
                ">=90",
        },

        "hyperparameters": {

            "learning_rate":
                0.08,

            "max_iter":
                150,

            "max_leaf_nodes":
                31,

            "min_samples_leaf":
                100,

            "l2_regularization":
                1.0,

            "max_bins":
                127,

            "early_stopping":
                False,

            "random_state":
                42,
        },

        "validation_results":
            validation_results,
    }

    metadata_path = (
        MODEL_DIR
        / "current_hourly_waterlogging_hgb_validation_metadata.json"
    )

    with open(
        metadata_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            metadata,
            file,
            indent=2,
        )

    print()
    print(
        f"✅ Metadata saved:"
    )

    print(
        metadata_path
    )

    # --------------------------------------------------------
    # Results CSV
    # --------------------------------------------------------

    results_path = (
        MODEL_DIR
        / "current_hourly_waterlogging_hgb_validation_results.csv"
    )

    results_df = pd.DataFrame(
        [validation_results]
    )

    results_df.to_csv(
        results_path,
        index=False,
    )

    print()
    print(
        f"✅ Results saved:"
    )

    print(
        results_path
    )

    # --------------------------------------------------------
    # Final
    # --------------------------------------------------------

    print()
    print("=" * 80)
    print(
        "✅ CURRENT-RISK HGB VALIDATION COMPLETE"
    )
    print("=" * 80)

    print()
    print(
        "Next step:"
    )

    print(
        "Review the 2024 validation metrics "
        "before training the final model."
    )


if __name__ == "__main__":
    main()