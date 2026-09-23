# ============================================================
# STEP 9: SMOTE OPTIMIZATION AND MODEL TRAINING
# ============================================================
#
# Purpose:
#   1. Load training and test data
#   2. Apply different SMOTE strategies
#   3. Train LightGBM and XGBoost models
#   4. Evaluate models on the untouched test set
#   5. Save complete preprocessing + SMOTE + model pipelines
#   6. Save model comparison metrics
#
# IMPORTANT:
#   - SMOTE is applied only to the training data.
#   - The test data is never oversampled.
#   - Models are saved as complete pipelines.
#   - Target labels are rule-based health-status labels.
#
# ============================================================

import json
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from lightgbm import LGBMClassifier
from xgboost import XGBClassifier


warnings.filterwarnings("ignore")


# ============================================================
# 1. PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

MODEL_OUTPUT_DIR = PROJECT_ROOT / "models" / "smote_models"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "step_9_smote"

MODEL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 2. CONFIGURATION
# ============================================================

TRAIN_DATA_PATH = PROCESSED_DATA_DIR / "train_dataset.csv"
TEST_DATA_PATH = PROCESSED_DATA_DIR / "test_dataset.csv"

TARGET_COLUMN = "Machine_Status_Code"

EXPECTED_CLASSES = [0, 1, 2]
CRITICAL_CLASS = 2
RANDOM_STATE = 42

TRAIN_LIGHTGBM = True
TRAIN_XGBOOST = True


# ============================================================
# 3. HELPER FUNCTIONS
# ============================================================

def print_section(title):
    """Print a formatted section heading."""

    print("\n" + "=" * 75)
    print(title)
    print("=" * 75)


def validate_target(y, dataset_name):
    """Validate target labels."""

    if y.isna().any():
        raise ValueError(
            f"{dataset_name} contains missing target values."
        )

    observed_classes = sorted(y.unique().tolist())

    if observed_classes != EXPECTED_CLASSES:
        raise ValueError(
            f"{dataset_name} has unexpected target classes.\n"
            f"Expected: {EXPECTED_CLASSES}\n"
            f"Observed: {observed_classes}"
        )


def load_data():
    """Load and validate training and test datasets."""

    print_section("LOADING DATA")

    if not TRAIN_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Training dataset not found:\n{TRAIN_DATA_PATH}"
        )

    if not TEST_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Test dataset not found:\n{TEST_DATA_PATH}"
        )

    train_data = pd.read_csv(TRAIN_DATA_PATH)
    test_data = pd.read_csv(TEST_DATA_PATH)

    if train_data.empty:
        raise ValueError("Training dataset is empty.")

    if test_data.empty:
        raise ValueError("Test dataset is empty.")

    if TARGET_COLUMN not in train_data.columns:
        raise ValueError(
            f"Target column '{TARGET_COLUMN}' was not found in "
            "the training dataset."
        )

    if TARGET_COLUMN not in test_data.columns:
        raise ValueError(
            f"Target column '{TARGET_COLUMN}' was not found in "
            "the test dataset."
        )

    X_train = train_data.drop(columns=[TARGET_COLUMN])
    y_train = train_data[TARGET_COLUMN].copy()

    X_test = test_data.drop(columns=[TARGET_COLUMN])
    y_test = test_data[TARGET_COLUMN].copy()

    if list(X_train.columns) != list(X_test.columns):
        raise ValueError(
            "Training and test feature columns do not match."
        )

    validate_target(y_train, "Training dataset")
    validate_target(y_test, "Test dataset")

    print(f"Training data shape: {train_data.shape}")
    print(f"Test data shape: {test_data.shape}")
    print(f"Target column: {TARGET_COLUMN}")
    print(f"Number of features: {X_train.shape[1]}")

    print("\nTraining target distribution:")
    print(y_train.value_counts().sort_index())

    print("\nTest target distribution:")
    print(y_test.value_counts().sort_index())

    return X_train, X_test, y_train, y_test


def create_preprocessor(X):
    """
    Create a preprocessing pipeline.

    Numerical columns:
        - Median imputation
        - Standard scaling

    Categorical columns:
        - Most-frequent imputation
        - One-hot encoding
    """

    numerical_columns = X.select_dtypes(
        include=["number", "bool"]
    ).columns.tolist()

    categorical_columns = X.select_dtypes(
        exclude=["number", "bool"]
    ).columns.tolist()

    numerical_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(strategy="median"),
            ),
            (
                "scaler",
                StandardScaler(),
            ),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(strategy="most_frequent"),
            ),
            (
                "encoder",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=False,
                ),
            ),
        ]
    )

    transformers = []

    if numerical_columns:
        transformers.append(
            (
                "numerical",
                numerical_pipeline,
                numerical_columns,
            )
        )

    if categorical_columns:
        transformers.append(
            (
                "categorical",
                categorical_pipeline,
                categorical_columns,
            )
        )

    if not transformers:
        raise ValueError(
            "No usable numerical or categorical features were found."
        )

    return ColumnTransformer(
        transformers=transformers,
        remainder="drop",
    )


def create_smote_strategy(y_train, strategy_name):
    """
    Create a safe SMOTE sampling strategy.

    Strategies:
        1. No_SMOTE
        2. SMOTE_Auto
        3. SMOTE_Critical_2x
    """

    class_counts = y_train.value_counts().to_dict()

    if strategy_name == "No_SMOTE":
        return None

    if strategy_name == "SMOTE_Auto":
        return "not majority"

    if strategy_name == "SMOTE_Critical_2x":
        critical_count = int(
            class_counts.get(CRITICAL_CLASS, 0)
        )

        if critical_count < 2:
            print(
                "[WARNING] Critical class has fewer than two "
                "samples. Critical-class SMOTE will be skipped."
            )
            return None

        majority_count = max(class_counts.values())

        target_count = min(
            critical_count * 2,
            majority_count,
        )

        if target_count <= critical_count:
            print(
                "[INFO] Critical class already meets the requested "
                "2x target. SMOTE will be skipped."
            )
            return None

        return {
            CRITICAL_CLASS: target_count
        }

    raise ValueError(
        f"Unknown SMOTE strategy: {strategy_name}"
    )


def calculate_smote_neighbors(y_train, strategy):
    """
    Calculate a safe k_neighbors value for SMOTE.

    SMOTE requires at least k_neighbors + 1 samples in
    each class being oversampled.
    """

    if strategy is None or isinstance(strategy, str):
        return 5

    target_classes = list(strategy.keys())
    class_counts = y_train.value_counts()

    available_counts = [
        int(class_counts.get(class_label, 0))
        for class_label in target_classes
    ]

    minimum_count = min(available_counts)

    if minimum_count < 2:
        raise ValueError(
            "A class selected for SMOTE has fewer than two samples."
        )

    return max(1, min(5, minimum_count - 1))


def create_model(model_name, number_of_classes):
    """Create the selected machine-learning model."""

    if model_name == "LightGBM":
        return LGBMClassifier(
            objective="multiclass",
            num_class=number_of_classes,
            n_estimators=300,
            learning_rate=0.05,
            max_depth=-1,
            num_leaves=31,
            subsample=0.8,
            subsample_freq=1,
            colsample_bytree=0.8,
            random_state=RANDOM_STATE,
            n_jobs=1,
            verbosity=-1,
        )

    if model_name == "XGBoost":
        return XGBClassifier(
            objective="multi:softprob",
            num_class=number_of_classes,
            n_estimators=300,
            learning_rate=0.05,
            max_depth=6,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=RANDOM_STATE,
            n_jobs=1,
            eval_metric="mlogloss",
        )

    raise ValueError(
        f"Unsupported model name: {model_name}"
    )


def build_pipeline(
    X_train,
    y_train,
    model_name,
    smote_strategy,
):
    """Build a complete preprocessing + SMOTE + model pipeline."""

    number_of_classes = len(EXPECTED_CLASSES)

    preprocessor = create_preprocessor(X_train)

    model = create_model(
        model_name=model_name,
        number_of_classes=number_of_classes,
    )

    pipeline_steps = [
        (
            "preprocessing",
            preprocessor,
        )
    ]

    if smote_strategy is not None:
        k_neighbors = calculate_smote_neighbors(
            y_train=y_train,
            strategy=smote_strategy,
        )

        smote = SMOTE(
            sampling_strategy=smote_strategy,
            k_neighbors=k_neighbors,
            random_state=RANDOM_STATE,
        )

        pipeline_steps.append(
            (
                "smote",
                smote,
            )
        )

        print(f"SMOTE k_neighbors: {k_neighbors}")

    pipeline_steps.append(
        (
            "model",
            model,
        )
    )

    return ImbPipeline(
        steps=pipeline_steps
    )


def evaluate_model(model, X_test, y_test):
    """Evaluate a trained model on the untouched test dataset."""

    predictions = model.predict(X_test)

    metrics = {
        "accuracy": accuracy_score(
            y_test,
            predictions,
        ),
        "balanced_accuracy": balanced_accuracy_score(
            y_test,
            predictions,
        ),
        "macro_precision": precision_score(
            y_test,
            predictions,
            labels=EXPECTED_CLASSES,
            average="macro",
            zero_division=0,
        ),
        "macro_recall": recall_score(
            y_test,
            predictions,
            labels=EXPECTED_CLASSES,
            average="macro",
            zero_division=0,
        ),
        "macro_f1_score": f1_score(
            y_test,
            predictions,
            labels=EXPECTED_CLASSES,
            average="macro",
            zero_division=0,
        ),
        "weighted_f1_score": f1_score(
            y_test,
            predictions,
            labels=EXPECTED_CLASSES,
            average="weighted",
            zero_division=0,
        ),
        "critical_precision": precision_score(
            y_test,
            predictions,
            labels=[CRITICAL_CLASS],
            average="macro",
            zero_division=0,
        ),
        "critical_recall": recall_score(
            y_test,
            predictions,
            labels=[CRITICAL_CLASS],
            average="macro",
            zero_division=0,
        ),
        "critical_f1_score": f1_score(
            y_test,
            predictions,
            labels=[CRITICAL_CLASS],
            average="macro",
            zero_division=0,
        ),
    }

    return predictions, metrics


def save_evaluation_outputs(
    model_name,
    strategy_name,
    model,
    predictions,
    y_test,
    metrics,
):
    """Save models, reports, metrics, and predictions."""

    file_prefix = f"{model_name}_{strategy_name}"

    model_path = MODEL_OUTPUT_DIR / f"{file_prefix}.joblib"
    joblib.dump(model, model_path)

    metrics_path = OUTPUT_DIR / f"{file_prefix}_metrics.json"

    with open(metrics_path, "w", encoding="utf-8") as file:
        json.dump(metrics, file, indent=4)

    report = classification_report(
        y_test,
        predictions,
        labels=EXPECTED_CLASSES,
        target_names=[
            "Healthy",
            "Warning",
            "Critical",
        ],
        zero_division=0,
        output_dict=True,
    )

    report_dataframe = pd.DataFrame(report).transpose()

    report_path = (
        OUTPUT_DIR / f"{file_prefix}_classification_report.csv"
    )
    report_dataframe.to_csv(report_path)

    matrix = confusion_matrix(
        y_test,
        predictions,
        labels=EXPECTED_CLASSES,
    )

    matrix_dataframe = pd.DataFrame(
        matrix,
        index=[
            "Actual_Healthy",
            "Actual_Warning",
            "Actual_Critical",
        ],
        columns=[
            "Predicted_Healthy",
            "Predicted_Warning",
            "Predicted_Critical",
        ],
    )

    matrix_path = (
        OUTPUT_DIR / f"{file_prefix}_confusion_matrix.csv"
    )
    matrix_dataframe.to_csv(matrix_path)

    prediction_dataframe = pd.DataFrame(
        {
            "actual_label": np.asarray(y_test),
            "predicted_label": np.asarray(predictions),
        }
    )

    prediction_dataframe["is_correct"] = (
        prediction_dataframe["actual_label"]
        == prediction_dataframe["predicted_label"]
    )

    prediction_path = (
        OUTPUT_DIR / f"{file_prefix}_predictions.csv"
    )

    prediction_dataframe.to_csv(
        prediction_path,
        index=False,
    )

    print(f"Model saved: {model_path}")
    print(f"Metrics saved: {metrics_path}")
    print(f"Report saved: {report_path}")
    print(f"Confusion matrix saved: {matrix_path}")
    print(f"Predictions saved: {prediction_path}")


# ============================================================
# 4. MAIN EXECUTION
# ============================================================

def main():
    print_section("STEP 9: SMOTE OPTIMIZATION")

    X_train, X_test, y_train, y_test = load_data()

    model_names = []

    if TRAIN_LIGHTGBM:
        model_names.append("LightGBM")

    if TRAIN_XGBOOST:
        model_names.append("XGBoost")

    if not model_names:
        raise ValueError(
            "No models have been enabled. "
            "Set TRAIN_LIGHTGBM or TRAIN_XGBOOST to True."
        )

    smote_strategies = [
        "No_SMOTE",
        "SMOTE_Auto",
        "SMOTE_Critical_2x",
    ]

    all_results = []

    for model_name in model_names:

        for strategy_name in smote_strategies:

            print_section(
                f"TRAINING: {model_name} | {strategy_name}"
            )

            try:
                smote_strategy = create_smote_strategy(
                    y_train=y_train,
                    strategy_name=strategy_name,
                )

                if smote_strategy is None:
                    print("SMOTE: Disabled")
                else:
                    print(f"SMOTE strategy: {smote_strategy}")

                model_pipeline = build_pipeline(
                    X_train=X_train,
                    y_train=y_train,
                    model_name=model_name,
                    smote_strategy=smote_strategy,
                )

                print("Training model...")

                model_pipeline.fit(
                    X_train,
                    y_train,
                )

                print(
                    "Evaluating model on untouched test data..."
                )

                predictions, metrics = evaluate_model(
                    model=model_pipeline,
                    X_test=X_test,
                    y_test=y_test,
                )

                metrics["model"] = model_name
                metrics["strategy"] = strategy_name
                metrics["smote_applied"] = (
                    smote_strategy is not None
                )

                all_results.append(metrics)

                print("\nEvaluation results:")

                for metric_name, metric_value in metrics.items():
                    if isinstance(metric_value, float):
                        print(
                            f"{metric_name}: {metric_value:.4f}"
                        )
                    else:
                        print(
                            f"{metric_name}: {metric_value}"
                        )

                save_evaluation_outputs(
                    model_name=model_name,
                    strategy_name=strategy_name,
                    model=model_pipeline,
                    predictions=predictions,
                    y_test=y_test,
                    metrics=metrics,
                )

            except Exception as error:
                print(
                    f"\n[FAILED] {model_name} - {strategy_name}"
                )
                print(f"Reason: {error}")

    if all_results:
        comparison_dataframe = pd.DataFrame(all_results)

        comparison_dataframe = comparison_dataframe.sort_values(
            by="macro_f1_score",
            ascending=False,
        ).reset_index(drop=True)

        comparison_path = (
            OUTPUT_DIR / "smote_model_comparison.csv"
        )

        comparison_dataframe.to_csv(
            comparison_path,
            index=False,
        )

        print_section("FINAL SMOTE COMPARISON")

        print(
            comparison_dataframe.to_string(index=False)
        )

        print(
            f"\nComparison file saved: {comparison_path}"
        )

    else:
        raise RuntimeError(
            "No model and SMOTE strategy completed successfully."
        )

    print_section("STEP 9 COMPLETED")

    print(f"Models directory: {MODEL_OUTPUT_DIR}")
    print(f"Output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()