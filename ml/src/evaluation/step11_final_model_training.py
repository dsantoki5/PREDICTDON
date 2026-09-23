
"""
STEP 11: FINAL MODEL SELECTION AND TRAINING

Purpose:
    1. Load processed training and test datasets.
    2. Split the training data into training and validation sets.
    3. Train LightGBM and XGBoost candidate models.
    4. Compare different SMOTE strategies.
    5. Select the best validation threshold using balanced metrics.
    6. Select the best overall model configuration.
    7. Retrain the selected model on the complete training dataset.
    8. Evaluate the final model on the untouched test dataset.
    9. Save the final model and evaluation reports.

Important:
    - The test set is not used for model or threshold selection.
    - SMOTE is applied only inside the training pipeline.
    - The final model is saved as a complete pipeline.
"""

import json
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
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from lightgbm import LGBMClassifier
from xgboost import XGBClassifier


# ============================================================
# 1. PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
FINAL_MODEL_DIR = PROJECT_ROOT / "models" / "final_models"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "step_11_final_model"

FINAL_MODEL_DIR.mkdir(parents=True, exist_ok=True)
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
VALIDATION_SIZE = 0.20

MODEL_NAMES = ["LightGBM", "XGBoost"]

SMOTE_STRATEGIES = [
    "No_SMOTE",
    "SMOTE_Auto",
    "SMOTE_Critical_2x",
]

THRESHOLDS = np.round(np.arange(0.05, 0.96, 0.05), 2)

# Minimum acceptable critical-class performance.
MINIMUM_CRITICAL_RECALL = 0.40
MINIMUM_CRITICAL_PRECISION = 0.50

# Weights for balanced model selection.
WEIGHT_ACCURACY = 0.30
WEIGHT_BALANCED_ACCURACY = 0.20
WEIGHT_MACRO_F1 = 0.20
WEIGHT_CRITICAL_F1 = 0.20
WEIGHT_CRITICAL_RECALL = 0.10


# ============================================================
# 3. GENERAL HELPERS
# ============================================================

def print_section(title):
    """Print a formatted section heading."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def validate_target_column(dataframe, dataset_name):
    """Validate the target column."""
    if TARGET_COLUMN not in dataframe.columns:
        raise ValueError(
            f"Target column '{TARGET_COLUMN}' was not found "
            f"in the {dataset_name} dataset."
        )


def validate_target_labels(target_values, dataset_name):
    """Validate the target labels."""
    actual_classes = sorted(
        pd.Series(target_values).dropna().unique().tolist()
    )

    if actual_classes != EXPECTED_CLASSES:
        raise ValueError(
            f"Unexpected classes in {dataset_name} dataset. "
            f"Expected {EXPECTED_CLASSES}, found {actual_classes}."
        )


# ============================================================
# 4. DATA LOADING
# ============================================================

def load_data():
    """Load and validate the training and test datasets."""

    print_section("LOADING DATA")

    if not TRAIN_DATA_PATH.exists():
        raise FileNotFoundError(f"Training dataset not found: {TRAIN_DATA_PATH}")

    if not TEST_DATA_PATH.exists():
        raise FileNotFoundError(f"Test dataset not found: {TEST_DATA_PATH}")

    train_data = pd.read_csv(TRAIN_DATA_PATH)
    test_data = pd.read_csv(TEST_DATA_PATH)

    validate_target_column(train_data, "training")
    validate_target_column(test_data, "test")

    X_train = train_data.drop(columns=[TARGET_COLUMN])
    y_train = train_data[TARGET_COLUMN].copy()

    X_test = test_data.drop(columns=[TARGET_COLUMN])
    y_test = test_data[TARGET_COLUMN].copy()

    if list(X_train.columns) != list(X_test.columns):
        raise ValueError("Training and test feature columns do not match.")

    validate_target_labels(y_train, "training")
    validate_target_labels(y_test, "test")

    print(f"Training shape: {train_data.shape}")
    print(f"Test shape: {test_data.shape}")
    print(f"Target column: {TARGET_COLUMN}")
    print(f"Feature count: {X_train.shape[1]}")

    print("\nTraining target distribution:")
    print(y_train.value_counts().sort_index())

    print("\nTest target distribution:")
    print(y_test.value_counts().sort_index())

    return train_data, test_data, X_train, X_test, y_train, y_test


# ============================================================
# 5. PREPROCESSING
# ============================================================

def create_preprocessor(X):
    """Create numerical and categorical preprocessing pipelines."""

    numerical_columns = X.select_dtypes(
        include=["number", "bool"]
    ).columns.tolist()

    categorical_columns = X.select_dtypes(
        exclude=["number", "bool"]
    ).columns.tolist()

    numerical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    try:
        encoder = OneHotEncoder(
            handle_unknown="ignore",
            sparse_output=False,
        )
    except TypeError:
        encoder = OneHotEncoder(
            handle_unknown="ignore",
            sparse=False,
        )

    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", encoder),
        ]
    )

    transformers = []

    if numerical_columns:
        transformers.append(
            ("numerical", numerical_pipeline, numerical_columns)
        )

    if categorical_columns:
        transformers.append(
            ("categorical", categorical_pipeline, categorical_columns)
        )

    if not transformers:
        raise ValueError("No usable feature columns were found.")

    return ColumnTransformer(
        transformers=transformers,
        remainder="drop",
    )


# ============================================================
# 6. SMOTE CONFIGURATION
# ============================================================

def create_smote_strategy(y_data, strategy_name):
    """Create the requested SMOTE sampling strategy."""

    class_counts = y_data.value_counts().to_dict()

    if strategy_name == "No_SMOTE":
        return None

    if strategy_name == "SMOTE_Auto":
        return "not majority"

    if strategy_name == "SMOTE_Critical_2x":
        critical_count = int(class_counts.get(CRITICAL_CLASS, 0))

        if critical_count < 2:
            return None

        majority_count = max(class_counts.values())
        desired_count = min(critical_count * 2, majority_count)

        if desired_count <= critical_count:
            return None

        return {CRITICAL_CLASS: desired_count}

    raise ValueError(f"Unknown SMOTE strategy: {strategy_name}")


def calculate_k_neighbors(y_data, sampling_strategy):
    """Calculate a safe SMOTE k_neighbors value."""

    if sampling_strategy is None or isinstance(sampling_strategy, str):
        return 5

    class_counts = y_data.value_counts()

    selected_counts = [
        int(class_counts.get(label, 0))
        for label in sampling_strategy.keys()
    ]

    if not selected_counts or min(selected_counts) < 2:
        raise ValueError("SMOTE requires at least two samples per target class.")

    return max(1, min(5, min(selected_counts) - 1))


# ============================================================
# 7. MODEL CREATION
# ============================================================

def create_model(model_name, number_of_classes):
    """Create a LightGBM or XGBoost classifier."""

    if model_name == "LightGBM":
        return LGBMClassifier(
            objective="multiclass",
            num_class=number_of_classes,
            n_estimators=300,
            learning_rate=0.05,
            max_depth=-1,
            num_leaves=31,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=RANDOM_STATE,
            n_jobs=-1,
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
            n_jobs=-1,
            eval_metric="mlogloss",
        )

    raise ValueError(f"Unsupported model: {model_name}")


def build_pipeline(X_data, y_data, model_name, strategy_name):
    """Build preprocessing, optional SMOTE, and model pipeline."""

    number_of_classes = y_data.nunique()

    sampling_strategy = create_smote_strategy(
        y_data,
        strategy_name,
    )

    preprocessing = create_preprocessor(X_data)
    model = create_model(model_name, number_of_classes)

    steps = [("preprocessing", preprocessing)]

    if sampling_strategy is not None:
        k_neighbors = calculate_k_neighbors(
            y_data,
            sampling_strategy,
        )

        steps.append(
            (
                "smote",
                SMOTE(
                    sampling_strategy=sampling_strategy,
                    k_neighbors=k_neighbors,
                    random_state=RANDOM_STATE,
                ),
            )
        )

    steps.append(("model", model))

    return ImbPipeline(steps=steps)


# ============================================================
# 8. PROBABILITY AND PREDICTION HELPERS
# ============================================================

def get_model_classes(model):
    """Retrieve class labels from the fitted pipeline."""

    if hasattr(model, "classes_"):
        return np.asarray(model.classes_)

    if hasattr(model, "named_steps"):
        for step_name in reversed(list(model.named_steps.keys())):
            step = model.named_steps[step_name]

            if hasattr(step, "classes_"):
                return np.asarray(step.classes_)

    raise AttributeError("Could not determine model class labels.")


def get_critical_probability_index(model):
    """Find the probability-column index of the critical class."""

    model_classes = get_model_classes(model)
    matching_indices = np.where(model_classes == CRITICAL_CLASS)[0]

    if len(matching_indices) == 0:
        raise ValueError(
            f"Critical class {CRITICAL_CLASS} is not present in model classes."
        )

    return int(matching_indices[0]), model_classes


def apply_critical_threshold(
    probabilities,
    model_classes,
    critical_probability_index,
    threshold,
):
    """
    Apply a critical probability threshold.

    A sample is marked critical when its critical probability
    reaches the configured threshold.
    """

    default_indices = np.argmax(probabilities, axis=1)
    predictions = model_classes[default_indices].copy()

    critical_probabilities = probabilities[:, critical_probability_index]
    critical_mask = critical_probabilities >= threshold

    predictions[critical_mask] = CRITICAL_CLASS

    return predictions


# ============================================================
# 9. METRICS AND MODEL-SELECTION SCORE
# ============================================================

def calculate_threshold_metrics(y_true, y_pred, threshold):
    """Calculate evaluation metrics for one threshold."""

    actual_critical = (
        np.asarray(y_true) == CRITICAL_CLASS
    ).astype(int)

    predicted_critical = (
        np.asarray(y_pred) == CRITICAL_CLASS
    ).astype(int)

    return {
        "threshold": float(threshold),
        "accuracy": accuracy_score(y_true, y_pred),
        "balanced_accuracy": balanced_accuracy_score(y_true, y_pred),
        "macro_f1_score": f1_score(
            y_true,
            y_pred,
            average="macro",
            zero_division=0,
        ),
        "critical_precision": precision_score(
            actual_critical,
            predicted_critical,
            zero_division=0,
        ),
        "critical_recall": recall_score(
            actual_critical,
            predicted_critical,
            zero_division=0,
        ),
        "critical_f1_score": f1_score(
            actual_critical,
            predicted_critical,
            zero_division=0,
        ),
        "critical_false_negatives": int(
            (
                (actual_critical == 1)
                & (predicted_critical == 0)
            ).sum()
        ),
        "critical_false_positives": int(
            (
                (actual_critical == 0)
                & (predicted_critical == 1)
            ).sum()
        ),
    }


def calculate_overall_model_score(metrics):
    """
    Calculate a balanced score for model selection.

    Accuracy is considered, but balanced accuracy, macro F1,
    and critical-class performance are also included.
    """

    return (
        WEIGHT_ACCURACY * metrics["accuracy"]
        + WEIGHT_BALANCED_ACCURACY * metrics["balanced_accuracy"]
        + WEIGHT_MACRO_F1 * metrics["macro_f1_score"]
        + WEIGHT_CRITICAL_F1 * metrics["critical_f1_score"]
        + WEIGHT_CRITICAL_RECALL * metrics["critical_recall"]
    )


def evaluate_validation_thresholds(model, X_validation, y_validation):
    """Evaluate all configured thresholds on validation data."""

    probabilities = model.predict_proba(X_validation)
    critical_index, model_classes = get_critical_probability_index(model)

    results = []

    for threshold in THRESHOLDS:
        predictions = apply_critical_threshold(
            probabilities=probabilities,
            model_classes=model_classes,
            critical_probability_index=critical_index,
            threshold=threshold,
        )

        results.append(
            calculate_threshold_metrics(
                y_true=y_validation,
                y_pred=predictions,
                threshold=threshold,
            )
        )

    return pd.DataFrame(results)


def select_final_threshold(validation_results):
    """
    Select the best threshold using minimum critical-class requirements.

    Eligible thresholds are compared using the balanced overall score.
    If no threshold is eligible, the highest overall-score threshold
    is selected as a fallback.
    """

    eligible_results = validation_results[
        (
            validation_results["critical_recall"]
            >= MINIMUM_CRITICAL_RECALL
        )
        & (
            validation_results["critical_precision"]
            >= MINIMUM_CRITICAL_PRECISION
        )
    ].copy()

    if not eligible_results.empty:
        selection_status = "Meets_Requirements"
        candidate_results = eligible_results
    else:
        selection_status = "Fallback_Best_Overall_Score"
        candidate_results = validation_results.copy()

    candidate_results["overall_model_score"] = candidate_results.apply(
        calculate_overall_model_score,
        axis=1,
    )

    selected_row = candidate_results.sort_values(
        by=[
            "overall_model_score",
            "macro_f1_score",
            "balanced_accuracy",
            "accuracy",
            "critical_f1_score",
        ],
        ascending=[False, False, False, False, False],
    ).iloc[0]

    return (
        float(selected_row["threshold"]),
        selection_status,
        selected_row,
    )


# ============================================================
# 10. FINAL TEST EVALUATION
# ============================================================

def evaluate_final_model(
    final_model,
    X_test,
    y_test,
    selected_threshold,
):
    """Evaluate the final model on the untouched test set."""

    probabilities = final_model.predict_proba(X_test)
    critical_index, model_classes = get_critical_probability_index(final_model)

    predictions = apply_critical_threshold(
        probabilities=probabilities,
        model_classes=model_classes,
        critical_probability_index=critical_index,
        threshold=selected_threshold,
    )

    actual_critical = (
        np.asarray(y_test) == CRITICAL_CLASS
    ).astype(int)

    predicted_critical = (
        np.asarray(predictions) == CRITICAL_CLASS
    ).astype(int)

    metrics = {
        "accuracy": accuracy_score(y_test, predictions),
        "balanced_accuracy": balanced_accuracy_score(y_test, predictions),
        "macro_f1_score": f1_score(
            y_test,
            predictions,
            average="macro",
            zero_division=0,
        ),
        "critical_precision": precision_score(
            actual_critical,
            predicted_critical,
            zero_division=0,
        ),
        "critical_recall": recall_score(
            actual_critical,
            predicted_critical,
            zero_division=0,
        ),
        "critical_f1_score": f1_score(
            actual_critical,
            predicted_critical,
            zero_division=0,
        ),
    }

    metrics["overall_model_score"] = calculate_overall_model_score(metrics)

    return predictions, probabilities, metrics


# ============================================================
# 11. OUTPUT SAVING
# ============================================================

def save_final_outputs(
    final_model,
    model_name,
    strategy_name,
    selected_threshold,
    selection_status,
    validation_results,
    final_predictions,
    final_probabilities,
    y_test,
    test_data,
    final_test_metrics,
):
    """Save the final model and all evaluation outputs."""

    model_filename = (
        f"{model_name}_{strategy_name.replace(' ', '_')}_Final.joblib"
    )

    model_path = FINAL_MODEL_DIR / model_filename
    joblib.dump(final_model, model_path)

    threshold_configuration = {
        "model_name": model_name,
        "smote_strategy": strategy_name,
        "critical_class": CRITICAL_CLASS,
        "selected_threshold": selected_threshold,
        "selection_status": selection_status,
        "minimum_critical_recall": MINIMUM_CRITICAL_RECALL,
        "minimum_critical_precision": MINIMUM_CRITICAL_PRECISION,
        "metric_weights": {
            "accuracy": WEIGHT_ACCURACY,
            "balanced_accuracy": WEIGHT_BALANCED_ACCURACY,
            "macro_f1_score": WEIGHT_MACRO_F1,
            "critical_f1_score": WEIGHT_CRITICAL_F1,
            "critical_recall": WEIGHT_CRITICAL_RECALL,
        },
        "threshold_selection_dataset": "validation",
        "final_evaluation_dataset": "test",
    }

    with open(
        OUTPUT_DIR / "final_threshold_configuration.json",
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(threshold_configuration, file, indent=4)

    validation_results.to_csv(
        OUTPUT_DIR / "validation_threshold_results.csv",
        index=False,
    )

    with open(
        OUTPUT_DIR / "final_test_metrics.json",
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(final_test_metrics, file, indent=4)

    report = classification_report(
        y_test,
        final_predictions,
        zero_division=0,
        output_dict=True,
    )

    pd.DataFrame(report).transpose().to_csv(
        OUTPUT_DIR / "final_test_classification_report.csv"
    )

    labels = sorted(
        set(np.asarray(y_test).tolist())
        | set(np.asarray(final_predictions).tolist())
    )

    matrix = confusion_matrix(
        y_test,
        final_predictions,
        labels=labels,
    )

    pd.DataFrame(
        matrix,
        index=[f"Actual_{label}" for label in labels],
        columns=[f"Predicted_{label}" for label in labels],
    ).to_csv(
        OUTPUT_DIR / "final_test_confusion_matrix.csv"
    )

    prediction_data = test_data.copy()

    prediction_data["actual_label"] = np.asarray(y_test)
    prediction_data["predicted_label"] = np.asarray(final_predictions)

    critical_index, _ = get_critical_probability_index(final_model)

    prediction_data["critical_probability"] = final_probabilities[
        :, critical_index
    ]

    prediction_data["is_correct"] = (
        prediction_data["actual_label"]
        == prediction_data["predicted_label"]
    )

    prediction_data.to_csv(
        OUTPUT_DIR / "final_test_predictions.csv",
        index=False,
    )

    print(f"Final model saved: {model_path}")
    print(
        "Threshold configuration saved: "
        f"{OUTPUT_DIR / 'final_threshold_configuration.json'}"
    )
    print(
        "Validation results saved: "
        f"{OUTPUT_DIR / 'validation_threshold_results.csv'}"
    )
    print(
        "Final metrics saved: "
        f"{OUTPUT_DIR / 'final_test_metrics.json'}"
    )
    print(
        "Classification report saved: "
        f"{OUTPUT_DIR / 'final_test_classification_report.csv'}"
    )
    print(
        "Confusion matrix saved: "
        f"{OUTPUT_DIR / 'final_test_confusion_matrix.csv'}"
    )
    print(
        "Test predictions saved: "
        f"{OUTPUT_DIR / 'final_test_predictions.csv'}"
    )


# ============================================================
# 12. MAIN EXECUTION
# ============================================================

def main():
    """Run the complete Step 11 workflow."""

    print_section("STEP 11: FINAL MODEL SELECTION AND TRAINING")

    (
        train_data,
        test_data,
        X_train,
        X_test,
        y_train,
        y_test,
    ) = load_data()

    (
        X_model_train,
        X_validation,
        y_model_train,
        y_validation,
    ) = train_test_split(
        X_train,
        y_train,
        test_size=VALIDATION_SIZE,
        random_state=RANDOM_STATE,
        stratify=y_train,
    )

    print_section("VALIDATION SPLIT")

    print(f"Model-training samples: {len(X_model_train)}")
    print(f"Validation samples: {len(X_validation)}")

    all_candidate_results = []
    best_candidate = None

    for model_name in MODEL_NAMES:
        for strategy_name in SMOTE_STRATEGIES:

            print_section(
                f"CANDIDATE: {model_name} | {strategy_name}"
            )

            try:
                candidate_model = build_pipeline(
                    X_data=X_model_train,
                    y_data=y_model_train,
                    model_name=model_name,
                    strategy_name=strategy_name,
                )

                print("Training candidate model...")
                candidate_model.fit(X_model_train, y_model_train)

                print("Evaluating validation thresholds...")

                validation_results = evaluate_validation_thresholds(
                    model=candidate_model,
                    X_validation=X_validation,
                    y_validation=y_validation,
                )

                (
                    selected_threshold,
                    selection_status,
                    selected_row,
                ) = select_final_threshold(validation_results)

                candidate_score = calculate_overall_model_score(
                    selected_row
                )

                candidate_summary = {
                    "model_name": model_name,
                    "smote_strategy": strategy_name,
                    "selected_threshold": selected_threshold,
                    "selection_status": selection_status,
                    "accuracy": float(selected_row["accuracy"]),
                    "balanced_accuracy": float(
                        selected_row["balanced_accuracy"]
                    ),
                    "macro_f1_score": float(
                        selected_row["macro_f1_score"]
                    ),
                    "critical_precision": float(
                        selected_row["critical_precision"]
                    ),
                    "critical_recall": float(
                        selected_row["critical_recall"]
                    ),
                    "critical_f1_score": float(
                        selected_row["critical_f1_score"]
                    ),
                    "overall_model_score": float(candidate_score),
                }

                all_candidate_results.append(candidate_summary)

                print(
                    f"Selected threshold: {selected_threshold:.2f}"
                )
                print(f"Selection status: {selection_status}")
                print(
                    f"Accuracy: {selected_row['accuracy']:.4f}"
                )
                print(
                    f"Balanced accuracy: "
                    f"{selected_row['balanced_accuracy']:.4f}"
                )
                print(
                    f"Macro F1: "
                    f"{selected_row['macro_f1_score']:.4f}"
                )
                print(
                    f"Critical precision: "
                    f"{selected_row['critical_precision']:.4f}"
                )
                print(
                    f"Critical recall: "
                    f"{selected_row['critical_recall']:.4f}"
                )
                print(
                    f"Critical F1: "
                    f"{selected_row['critical_f1_score']:.4f}"
                )
                print(
                    f"Overall score: {candidate_score:.4f}"
                )

                candidate_rank = (
                    1 if selection_status == "Meets_Requirements" else 0,
                    candidate_score,
                    float(selected_row["macro_f1_score"]),
                    float(selected_row["balanced_accuracy"]),
                    float(selected_row["accuracy"]),
                    float(selected_row["critical_f1_score"]),
                )

                if (
                    best_candidate is None
                    or candidate_rank > best_candidate["rank"]
                ):
                    best_candidate = {
                        "rank": candidate_rank,
                        "model_name": model_name,
                        "strategy_name": strategy_name,
                        "threshold": selected_threshold,
                        "validation_results": validation_results,
                        "selection_status": selection_status,
                        "overall_model_score": candidate_score,
                    }

            except Exception as error:
                print(
                    f"[FAILED] {model_name} | {strategy_name}"
                )
                print(f"Reason: {error}")

    if best_candidate is None:
        raise RuntimeError("No candidate model completed successfully.")

    comparison_dataframe = pd.DataFrame(all_candidate_results)

    comparison_path = OUTPUT_DIR / "candidate_model_comparison.csv"
    comparison_dataframe.to_csv(comparison_path, index=False)

    print(f"\nCandidate comparison saved: {comparison_path}")

    print_section("SELECTED FINAL CONFIGURATION")

    print(f"Model: {best_candidate['model_name']}")
    print(f"SMOTE strategy: {best_candidate['strategy_name']}")
    print(f"Threshold: {best_candidate['threshold']:.2f}")
    print(f"Status: {best_candidate['selection_status']}")
    print(
        f"Overall score: "
        f"{best_candidate['overall_model_score']:.4f}"
    )

    print_section("RETRAINING ON COMPLETE TRAINING DATA")

    final_model = build_pipeline(
        X_data=X_train,
        y_data=y_train,
        model_name=best_candidate["model_name"],
        strategy_name=best_candidate["strategy_name"],
    )

    final_model.fit(X_train, y_train)

    print("Final model training completed.")

    print_section("FINAL TEST EVALUATION")

    (
        final_predictions,
        final_probabilities,
        final_test_metrics,
    ) = evaluate_final_model(
        final_model=final_model,
        X_test=X_test,
        y_test=y_test,
        selected_threshold=best_candidate["threshold"],
    )

    print("\nFinal test metrics:")

    for metric_name, metric_value in final_test_metrics.items():
        print(f"{metric_name}: {metric_value:.4f}")

    save_final_outputs(
        final_model=final_model,
        model_name=best_candidate["model_name"],
        strategy_name=best_candidate["strategy_name"],
        selected_threshold=best_candidate["threshold"],
        selection_status=best_candidate["selection_status"],
        validation_results=best_candidate["validation_results"],
        final_predictions=final_predictions,
        final_probabilities=final_probabilities,
        y_test=y_test,
        test_data=test_data,
        final_test_metrics=final_test_metrics,
    )

    print_section("STEP 11 COMPLETED")

    print(f"Final model directory: {FINAL_MODEL_DIR}")
    print(f"Output directory: {OUTPUT_DIR}")
    print("You can now use the saved final model in Step 12.")


if __name__ == "__main__":
    main()