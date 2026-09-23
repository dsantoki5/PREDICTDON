"""
Step 10: Threshold Evaluation and Critical Alert Analysis

Purpose:
- Load the test dataset.
- Load the trained LightGBM + SMOTE pipeline.
- Evaluate default argmax predictions.
- Evaluate critical-class probability thresholds.
- Compare macro F1 and critical-class recall.
- Save threshold metrics and prediction outputs.

Important:
Threshold evaluation is exploratory because thresholds are evaluated
on the test dataset. The selected threshold must be validated on a
separate validation dataset before production deployment.
"""

from pathlib import Path
import json

import joblib
import numpy as np
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
)


# ============================================================
# 1. PROJECT PATHS AND CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

TEST_DATA_PATH = (
    PROJECT_ROOT / "data" / "processed" / "test_dataset.csv"
)

MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "smote_models"
    / "LightGBM_SMOTE_Critical_2x.joblib"
)

EVALUATION_DIR = PROJECT_ROOT / "reports" / "evaluation"

THRESHOLD_METRICS_PATH = (
    EVALUATION_DIR / "threshold_metrics.csv"
)

THRESHOLD_SUMMARY_PATH = (
    EVALUATION_DIR / "threshold_summary.json"
)

PREDICTIONS_PATH = (
    EVALUATION_DIR / "threshold_predictions.csv"
)


# ============================================================
# 2. MODEL AND TARGET CONFIGURATION
# ============================================================

TARGET_COLUMN = "Machine_Status_Code"

EXPECTED_CLASSES = [0, 1, 2]

CRITICAL_CLASS = 2

DEFAULT_THRESHOLD = None

THRESHOLDS = np.round(
    np.arange(0.05, 0.96, 0.05),
    2,
)


# ============================================================
# 3. DATA LOADING
# ============================================================

def load_test_data():
    """
    Load the processed test dataset and separate features and target.
    """

    if not TEST_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Test dataset not found: {TEST_DATA_PATH}"
        )

    test_data = pd.read_csv(TEST_DATA_PATH)

    if TARGET_COLUMN not in test_data.columns:
        raise ValueError(
            f"Target column '{TARGET_COLUMN}' was not found "
            f"in the test dataset."
        )

    X_test = test_data.drop(columns=[TARGET_COLUMN])
    y_test = test_data[TARGET_COLUMN]

    validate_target_labels(y_test, "test dataset")

    print(f"Test dataset loaded: {test_data.shape}")
    print(f"Feature shape: {X_test.shape}")
    print(f"Target column: {TARGET_COLUMN}")
    print(f"Target distribution:\n{y_test.value_counts().sort_index()}")

    return test_data, X_test, y_test


def validate_target_labels(y, dataset_name):
    """
    Validate that the target contains the expected class labels.
    """

    actual_classes = sorted(pd.Series(y).dropna().unique().tolist())

    if actual_classes != EXPECTED_CLASSES:
        raise ValueError(
            f"Unexpected classes in {dataset_name}. "
            f"Expected {EXPECTED_CLASSES}, found {actual_classes}."
        )


# ============================================================
# 4. MODEL LOADING
# ============================================================

def load_model():
    """
    Load the trained model pipeline.
    """

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model file not found: {MODEL_PATH}"
        )

    model = joblib.load(MODEL_PATH)

    if not hasattr(model, "predict_proba"):
        raise AttributeError(
            "The loaded model does not support predict_proba()."
        )

    print(f"Model loaded: {MODEL_PATH.name}")

    return model


def get_model_classes(model):
    """
    Extract class labels from the trained model or pipeline.
    """

    if hasattr(model, "classes_"):
        model_classes = model.classes_

    elif hasattr(model, "named_steps"):
        final_step = list(model.named_steps.values())[-1]

        if not hasattr(final_step, "classes_"):
            raise AttributeError(
                "Could not find classes_ in the final pipeline step."
            )

        model_classes = final_step.classes_

    else:
        raise AttributeError(
            "Could not determine model classes."
        )

    model_classes = np.asarray(model_classes).tolist()

    if model_classes != EXPECTED_CLASSES:
        raise ValueError(
            f"Unexpected model classes. "
            f"Expected {EXPECTED_CLASSES}, found {model_classes}."
        )

    return model_classes


# ============================================================
# 5. PREDICTION FUNCTIONS
# ============================================================

def generate_predictions(model, X_test):
    """
    Generate class probabilities and default argmax predictions.
    """

    probabilities = model.predict_proba(X_test)
    probabilities = np.asarray(probabilities)

    if probabilities.ndim != 2:
        raise ValueError(
            "Model probabilities must be a 2-dimensional array."
        )

    if probabilities.shape[1] != len(EXPECTED_CLASSES):
        raise ValueError(
            "The number of probability columns does not match "
            f"the expected number of classes: {EXPECTED_CLASSES}."
        )

    if not np.isfinite(probabilities).all():
        raise ValueError(
            "Model probabilities contain invalid values."
        )

    default_predictions = np.argmax(
        probabilities,
        axis=1,
    )

    return probabilities, default_predictions


def apply_critical_threshold(
    probabilities,
    default_predictions,
    model_classes,
    threshold,
):
    """
    Apply a critical-class probability override.

    If the probability of the critical class is greater than or
    equal to the threshold, the prediction is changed to the
    critical class.

    This rule only adds critical alerts. It does not remove a
    critical prediction produced by the default argmax method.
    """

    if CRITICAL_CLASS not in model_classes:
        raise ValueError(
            f"Critical class {CRITICAL_CLASS} was not found "
            f"in model classes: {model_classes}"
        )

    critical_index = model_classes.index(CRITICAL_CLASS)

    critical_probabilities = probabilities[:, critical_index]

    threshold_predictions = default_predictions.copy()

    critical_mask = critical_probabilities >= threshold

    threshold_predictions[critical_mask] = CRITICAL_CLASS

    return threshold_predictions


# ============================================================
# 6. METRIC CALCULATION
# ============================================================

def calculate_metrics(
    y_true,
    y_pred,
    threshold=None,
    threshold_type="Critical_Override",
):
    """
    Calculate classification metrics for a prediction strategy.
    """

    metrics = {
        "threshold": threshold,
        "threshold_type": threshold_type,
        "accuracy": accuracy_score(y_true, y_pred),
        "macro_precision": precision_score(
            y_true,
            y_pred,
            average="macro",
            zero_division=0,
        ),
        "macro_recall": recall_score(
            y_true,
            y_pred,
            average="macro",
            zero_division=0,
        ),
        "macro_f1": f1_score(
            y_true,
            y_pred,
            average="macro",
            zero_division=0,
        ),
        "critical_precision": precision_score(
            y_true,
            y_pred,
            labels=[CRITICAL_CLASS],
            average="macro",
            zero_division=0,
        ),
        "critical_recall": recall_score(
            y_true,
            y_pred,
            labels=[CRITICAL_CLASS],
            average="macro",
            zero_division=0,
        ),
        "critical_f1": f1_score(
            y_true,
            y_pred,
            labels=[CRITICAL_CLASS],
            average="macro",
            zero_division=0,
        ),
    }

    return metrics


# ============================================================
# 7. THRESHOLD EVALUATION
# ============================================================

def evaluate_thresholds(
    model,
    X_test,
    y_test,
    model_classes,
):
    """
    Evaluate default argmax predictions and critical thresholds.
    """

    probabilities, default_predictions = generate_predictions(
        model,
        X_test,
    )

    results = []

    default_metrics = calculate_metrics(
        y_test,
        default_predictions,
        threshold=DEFAULT_THRESHOLD,
        threshold_type="Default_Argmax",
    )

    results.append(default_metrics)

    for threshold in THRESHOLDS:

        threshold_predictions = apply_critical_threshold(
            probabilities=probabilities,
            default_predictions=default_predictions,
            model_classes=model_classes,
            threshold=threshold,
        )

        threshold_metrics = calculate_metrics(
            y_test,
            threshold_predictions,
            threshold=float(threshold),
            threshold_type="Critical_Override",
        )

        results.append(threshold_metrics)

    results_df = pd.DataFrame(results)

    return (
        results_df,
        probabilities,
        default_predictions,
    )


# ============================================================
# 8. OUTPUT SAVING
# ============================================================

def save_threshold_predictions(
    test_data,
    y_test,
    probabilities,
    default_predictions,
    model_classes,
    threshold,
):
    """
    Save row-level predictions for the selected threshold.
    """

    threshold_predictions = apply_critical_threshold(
        probabilities=probabilities,
        default_predictions=default_predictions,
        model_classes=model_classes,
        threshold=threshold,
    )

    prediction_data = test_data.drop(
        columns=[TARGET_COLUMN]
    ).copy()

    prediction_data["actual_label"] = y_test.to_numpy()
    prediction_data["default_prediction"] = default_predictions
    prediction_data["threshold_prediction"] = threshold_predictions

    critical_index = model_classes.index(CRITICAL_CLASS)

    prediction_data["critical_probability"] = (
        probabilities[:, critical_index]
    )

    prediction_data["threshold"] = threshold

    prediction_data.to_csv(
        PREDICTIONS_PATH,
        index=False,
    )

    print(
        f"Threshold predictions saved to: {PREDICTIONS_PATH}"
    )


def save_summary(results_df):
    """
    Save exploratory threshold summary.

    The best thresholds are selected only for analysis and must not
    be treated as production thresholds without validation.
    """

    threshold_only_results = results_df[
        results_df["threshold_type"] == "Critical_Override"
    ].copy()

    best_macro_f1_row = threshold_only_results.loc[
        threshold_only_results["macro_f1"].idxmax()
    ]

    best_critical_recall_row = threshold_only_results.loc[
        threshold_only_results["critical_recall"].idxmax()
    ]

    summary = {
        "warning": (
            "Thresholds were evaluated on the test dataset for "
            "exploratory analysis only. Validate any selected "
            "threshold on a separate validation dataset before "
            "production deployment."
        ),
        "best_macro_f1_threshold": float(
            best_macro_f1_row["threshold"]
        ),
        "best_macro_f1": float(
            best_macro_f1_row["macro_f1"]
        ),
        "best_critical_recall_threshold": float(
            best_critical_recall_row["threshold"]
        ),
        "best_critical_recall": float(
            best_critical_recall_row["critical_recall"]
        ),
    }

    with open(
        THRESHOLD_SUMMARY_PATH,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            summary,
            file,
            indent=4,
        )

    print(
        f"Threshold summary saved to: {THRESHOLD_SUMMARY_PATH}"
    )


# ============================================================
# 9. MAIN EXECUTION
# ============================================================

def main():
    """
    Run the complete threshold evaluation workflow.
    """

    print("=" * 70)
    print("STEP 10: THRESHOLD EVALUATION")
    print("=" * 70)

    EVALUATION_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    test_data, X_test, y_test = load_test_data()

    model = load_model()

    model_classes = get_model_classes(model)

    print(f"Model classes: {model_classes}")

    (
        results_df,
        probabilities,
        default_predictions,
    ) = evaluate_thresholds(
        model=model,
        X_test=X_test,
        y_test=y_test,
        model_classes=model_classes,
    )

    results_df.to_csv(
        THRESHOLD_METRICS_PATH,
        index=False,
    )

    print(
        f"Threshold metrics saved to: {THRESHOLD_METRICS_PATH}"
    )

    save_summary(results_df)

    selected_threshold = 0.50

    save_threshold_predictions(
        test_data=test_data,
        y_test=y_test,
        probabilities=probabilities,
        default_predictions=default_predictions,
        model_classes=model_classes,
        threshold=selected_threshold,
    )

    print("\nThreshold evaluation results:")
    print(results_df.to_string(index=False))

    print("\nStep 10 completed successfully.")


if __name__ == "__main__":
    main()