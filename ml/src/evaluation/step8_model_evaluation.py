# ============================================================
# STEP 8: MODEL EVALUATION AND ERROR ANALYSIS
# ============================================================
#
# Purpose:
#   1. Load the prepared test dataset
#   2. Load tuned models
#   3. Evaluate model performance
#   4. Generate classification reports
#   5. Generate confusion matrices
#   6. Analyze critical-class predictions
#   7. Save evaluation results and error analysis
#
# Supported models:
#   - LightGBM
#   - XGBoost
#   - Random Forest
#
# ============================================================

import json
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    ConfusionMatrixDisplay,
)

warnings.filterwarnings("ignore")


# ============================================================
# 1. PROJECT PATHS
# ============================================================

# File location:
# project_root/src/evaluation/step8_model_evaluation.py
#
# parents[0] = evaluation
# parents[1] = src
# parents[2] = project root

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
MODEL_DIR = PROJECT_ROOT / "models" / "tuned_models"

OUTPUT_DIR = PROJECT_ROOT / "outputs" / "step_8_evaluation"
REPORT_DIR = OUTPUT_DIR / "reports"
PLOT_DIR = OUTPUT_DIR / "plots"
PREDICTION_DIR = OUTPUT_DIR / "predictions"

REPORT_DIR.mkdir(parents=True, exist_ok=True)
PLOT_DIR.mkdir(parents=True, exist_ok=True)
PREDICTION_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 2. CONFIGURATION
# ============================================================

TEST_DATA_PATH = DATA_DIR / "processed" / "test_dataset.csv"

TARGET_COLUMN = "Machine_Status_Code"

CRITICAL_CLASS = 2

CLASS_LABELS = [0, 1, 2]

MODEL_FILES = {
    "LightGBM": [
        "LightGBM.joblib",
        "lightgbm.joblib",
        "lgbm.joblib",
    ],
    "XGBoost": [
        "XGBoost.joblib",
        "xgboost.joblib",
        "xgb.joblib",
    ],
    "Random_Forest": [
        "Random_Forest.joblib",
        "RandomForest.joblib",
        "random_forest.joblib",
        "randomforest.joblib",
    ],
}


# ============================================================
# 3. HELPER FUNCTIONS
# ============================================================

def print_section(title):
    """Print a formatted section heading."""

    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def load_test_data():
    """
    Load the prepared test dataset and separate features and target.
    """

    print_section("LOADING TEST DATA")

    if not TEST_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Test dataset was not found:\n{TEST_DATA_PATH}"
        )

    test_data = pd.read_csv(TEST_DATA_PATH)

    if test_data.empty:
        raise ValueError("The test dataset is empty.")

    if TARGET_COLUMN not in test_data.columns:
        raise ValueError(
            f"Target column '{TARGET_COLUMN}' was not found.\n"
            f"Available columns:\n{list(test_data.columns)}"
        )

    X_test = test_data.drop(columns=[TARGET_COLUMN]).copy()
    y_test = pd.to_numeric(
        test_data[TARGET_COLUMN],
        errors="raise",
    ).astype(int)

    if sorted(y_test.unique().tolist()) != CLASS_LABELS:
        raise ValueError(
            "Unexpected target classes in the test dataset. "
            f"Found: {sorted(y_test.unique().tolist())}; "
            f"Expected: {CLASS_LABELS}"
        )

    print(f"Test dataset: {TEST_DATA_PATH}")
    print(f"Dataset shape: {test_data.shape}")
    print(f"Target column: {TARGET_COLUMN}")
    print(f"Feature count: {X_test.shape[1]}")
    print(f"Test samples: {len(X_test)}")

    print("\nTarget distribution:")
    print(y_test.value_counts().sort_index())

    return test_data, X_test, y_test


def find_model_file(model_name):
    """Search for a model file using possible filenames."""

    for filename in MODEL_FILES.get(model_name, []):
        model_path = MODEL_DIR / filename

        if model_path.exists():
            return model_path

    return None


def load_models():
    """Load all available tuned models."""

    print_section("LOADING TRAINED MODELS")

    if not MODEL_DIR.exists():
        raise FileNotFoundError(
            f"Model directory was not found:\n{MODEL_DIR}"
        )

    loaded_models = {}

    for model_name in MODEL_FILES:
        model_path = find_model_file(model_name)

        if model_path is None:
            print(f"[SKIPPED] {model_name}: model file not found")
            continue

        try:
            model = joblib.load(model_path)
            loaded_models[model_name] = model

            print(f"[LOADED] {model_name}")
            print(f"        File: {model_path}")

        except Exception as error:
            print(
                f"[ERROR] Could not load {model_name}: {error}"
            )

    if not loaded_models:
        raise FileNotFoundError(
            "No trained models were found.\n"
            f"Expected directory:\n{MODEL_DIR}"
        )

    return loaded_models


def get_model_classes(model):
    """
    Extract class labels from a model whenever possible.
    """

    if hasattr(model, "classes_"):
        return np.asarray(model.classes_)

    if hasattr(model, "named_steps"):
        for step_name in reversed(
            list(model.named_steps.keys())
        ):
            step = model.named_steps[step_name]

            if hasattr(step, "classes_"):
                return np.asarray(step.classes_)

    return np.asarray(CLASS_LABELS)


def predict_with_model(model, X_test):
    """
    Generate predictions and class probabilities.
    """

    try:
        predictions = model.predict(X_test)

    except Exception as error:
        raise RuntimeError(
            "The model could not predict using the test features.\n"
            "Verify that the test dataset has the same 44 features "
            "used during model training.\n\n"
            f"Original error: {error}"
        ) from error

    probabilities = None

    if hasattr(model, "predict_proba"):
        try:
            probabilities = model.predict_proba(X_test)
        except Exception:
            probabilities = None

    return np.asarray(predictions), probabilities


def calculate_critical_metrics(y_true, y_pred):
    """Calculate metrics for the Critical class."""

    critical_true = (
        np.asarray(y_true) == CRITICAL_CLASS
    ).astype(int)

    critical_pred = (
        np.asarray(y_pred) == CRITICAL_CLASS
    ).astype(int)

    return {
        "critical_class": CRITICAL_CLASS,
        "critical_precision": precision_score(
            critical_true,
            critical_pred,
            zero_division=0,
        ),
        "critical_recall": recall_score(
            critical_true,
            critical_pred,
            zero_division=0,
        ),
        "critical_f1_score": f1_score(
            critical_true,
            critical_pred,
            zero_division=0,
        ),
        "critical_actual_count": int(critical_true.sum()),
        "critical_predicted_count": int(critical_pred.sum()),
    }


def calculate_model_metrics(
    y_true,
    y_pred,
    probabilities,
    model,
):
    """Calculate general and Critical-class metrics."""

    metrics = {
        "accuracy": accuracy_score(y_true, y_pred),
        "balanced_accuracy": balanced_accuracy_score(
            y_true,
            y_pred,
        ),
        "macro_precision": precision_score(
            y_true,
            y_pred,
            labels=CLASS_LABELS,
            average="macro",
            zero_division=0,
        ),
        "macro_recall": recall_score(
            y_true,
            y_pred,
            labels=CLASS_LABELS,
            average="macro",
            zero_division=0,
        ),
        "macro_f1_score": f1_score(
            y_true,
            y_pred,
            labels=CLASS_LABELS,
            average="macro",
            zero_division=0,
        ),
        "weighted_f1_score": f1_score(
            y_true,
            y_pred,
            labels=CLASS_LABELS,
            average="weighted",
            zero_division=0,
        ),
    }

    metrics.update(
        calculate_critical_metrics(y_true, y_pred)
    )

    if probabilities is not None:
        try:
            model_classes = get_model_classes(model)

            if len(model_classes) == 2:
                metrics["roc_auc"] = roc_auc_score(
                    y_true,
                    probabilities[:, 1],
                )

            elif len(model_classes) == 3:
                metrics["roc_auc_ovr_macro"] = roc_auc_score(
                    y_true,
                    probabilities,
                    multi_class="ovr",
                    average="macro",
                    labels=model_classes,
                )

        except Exception as error:
            print(
                "[WARNING] ROC-AUC could not be calculated: "
                f"{error}"
            )

    return metrics


def save_classification_report(
    model_name,
    y_true,
    y_pred,
):
    """Save the classification report as CSV and JSON."""

    report_dictionary = classification_report(
        y_true,
        y_pred,
        labels=CLASS_LABELS,
        zero_division=0,
        output_dict=True,
    )

    report_dataframe = pd.DataFrame(
        report_dictionary
    ).transpose()

    csv_path = (
        REPORT_DIR
        / f"{model_name}_classification_report.csv"
    )

    json_path = (
        REPORT_DIR
        / f"{model_name}_classification_report.json"
    )

    report_dataframe.to_csv(csv_path)

    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(
            report_dictionary,
            file,
            indent=4,
        )

    print(f"Classification report saved: {csv_path}")


def save_confusion_matrix(
    model_name,
    y_true,
    y_pred,
):
    """Generate and save the confusion matrix plot and CSV."""

    matrix = confusion_matrix(
        y_true,
        y_pred,
        labels=CLASS_LABELS,
    )

    matrix_dataframe = pd.DataFrame(
        matrix,
        index=[
            f"Actual_{label}"
            for label in CLASS_LABELS
        ],
        columns=[
            f"Predicted_{label}"
            for label in CLASS_LABELS
        ],
    )

    matrix_csv_path = (
        REPORT_DIR
        / f"{model_name}_confusion_matrix.csv"
    )

    matrix_dataframe.to_csv(matrix_csv_path)

    figure, axis = plt.subplots(figsize=(7, 6))

    display = ConfusionMatrixDisplay(
        confusion_matrix=matrix,
        display_labels=CLASS_LABELS,
    )

    display.plot(
        ax=axis,
        values_format="d",
        colorbar=False,
    )

    axis.set_title(
        f"{model_name} - Confusion Matrix"
    )
    axis.set_xlabel("Predicted Label")
    axis.set_ylabel("Actual Label")

    figure.tight_layout()

    plot_path = (
        PLOT_DIR
        / f"{model_name}_confusion_matrix.png"
    )

    figure.savefig(
        plot_path,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close(figure)

    print(f"Confusion matrix saved: {plot_path}")


def get_probability_class_labels(
    probabilities,
    model,
):
    """Return class labels corresponding to probability columns."""

    model_classes = get_model_classes(model)

    if len(model_classes) == probabilities.shape[1]:
        return model_classes.tolist()

    return list(range(probabilities.shape[1]))


def save_error_analysis(
    model_name,
    original_test_data,
    y_true,
    y_pred,
    probabilities,
    model,
):
    """Save incorrectly predicted samples for further analysis."""

    error_mask = (
        np.asarray(y_true) != np.asarray(y_pred)
    )

    error_data = original_test_data.loc[
        error_mask
    ].copy()

    error_data["actual_label"] = (
        np.asarray(y_true)[error_mask]
    )

    error_data["predicted_label"] = (
        np.asarray(y_pred)[error_mask]
    )

    if probabilities is not None:
        class_labels = get_probability_class_labels(
            probabilities,
            model,
        )

        for index, class_label in enumerate(class_labels):
            error_data[
                f"probability_class_{class_label}"
            ] = probabilities[error_mask, index]

    error_data["is_critical_actual"] = (
        error_data["actual_label"] == CRITICAL_CLASS
    )

    error_data["is_critical_predicted"] = (
        error_data["predicted_label"] == CRITICAL_CLASS
    )

    error_path = (
        PREDICTION_DIR
        / f"{model_name}_error_analysis.csv"
    )

    error_data.to_csv(
        error_path,
        index=False,
    )

    print(f"Error analysis saved: {error_path}")
    print(f"Incorrect predictions: {len(error_data)}")

    return error_data


def save_prediction_results(
    model_name,
    original_test_data,
    y_true,
    y_pred,
    probabilities,
    model,
):
    """Save predictions for every test sample."""

    prediction_data = original_test_data.copy()

    prediction_data["actual_label"] = (
        np.asarray(y_true)
    )

    prediction_data["predicted_label"] = (
        np.asarray(y_pred)
    )

    prediction_data["is_correct"] = (
        prediction_data["actual_label"]
        == prediction_data["predicted_label"]
    )

    prediction_data["actual_is_critical"] = (
        prediction_data["actual_label"] == CRITICAL_CLASS
    )

    prediction_data["predicted_is_critical"] = (
        prediction_data["predicted_label"] == CRITICAL_CLASS
    )

    if probabilities is not None:
        class_labels = get_probability_class_labels(
            probabilities,
            model,
        )

        for index, class_label in enumerate(class_labels):
            prediction_data[
                f"probability_class_{class_label}"
            ] = probabilities[:, index]

    prediction_path = (
        PREDICTION_DIR
        / f"{model_name}_test_predictions.csv"
    )

    prediction_data.to_csv(
        prediction_path,
        index=False,
    )

    print(f"Prediction results saved: {prediction_path}")


def evaluate_model(
    model_name,
    model,
    original_test_data,
    X_test,
    y_test,
):
    """Evaluate one model and save all related outputs."""

    print_section(f"EVALUATING {model_name}")

    y_pred, probabilities = predict_with_model(
        model,
        X_test,
    )

    metrics = calculate_model_metrics(
        y_true=y_test,
        y_pred=y_pred,
        probabilities=probabilities,
        model=model,
    )

    print("\nEvaluation metrics:")

    for metric_name, metric_value in metrics.items():
        if isinstance(metric_value, (float, np.floating)):
            print(f"{metric_name}: {metric_value:.4f}")
        else:
            print(f"{metric_name}: {metric_value}")

    metrics_path = (
        REPORT_DIR
        / f"{model_name}_metrics.json"
    )

    with open(metrics_path, "w", encoding="utf-8") as file:
        json.dump(
            metrics,
            file,
            indent=4,
            default=float,
        )

    save_classification_report(
        model_name=model_name,
        y_true=y_test,
        y_pred=y_pred,
    )

    save_confusion_matrix(
        model_name=model_name,
        y_true=y_test,
        y_pred=y_pred,
    )

    save_prediction_results(
        model_name=model_name,
        original_test_data=original_test_data,
        y_true=y_test,
        y_pred=y_pred,
        probabilities=probabilities,
        model=model,
    )

    save_error_analysis(
        model_name=model_name,
        original_test_data=original_test_data,
        y_true=y_test,
        y_pred=y_pred,
        probabilities=probabilities,
        model=model,
    )

    return metrics


# ============================================================
# 4. MAIN EXECUTION
# ============================================================

def main():
    print_section(
        "STEP 8: MODEL EVALUATION AND ERROR ANALYSIS"
    )

    test_data, X_test, y_test = load_test_data()

    models = load_models()

    all_metrics = []

    for model_name, model in models.items():
        try:
            metrics = evaluate_model(
                model_name=model_name,
                model=model,
                original_test_data=test_data,
                X_test=X_test,
                y_test=y_test,
            )

            metrics["model"] = model_name
            all_metrics.append(metrics)

        except Exception as error:
            print(
                f"\n[FAILED] Evaluation failed for "
                f"{model_name}."
            )
            print(f"Reason: {error}")

    if all_metrics:
        comparison_dataframe = pd.DataFrame(
            all_metrics
        )

        comparison_columns = [
            "model",
            "accuracy",
            "balanced_accuracy",
            "macro_precision",
            "macro_recall",
            "macro_f1_score",
            "weighted_f1_score",
            "critical_precision",
            "critical_recall",
            "critical_f1_score",
            "critical_actual_count",
            "critical_predicted_count",
            "roc_auc_ovr_macro",
        ]

        existing_columns = [
            column
            for column in comparison_columns
            if column in comparison_dataframe.columns
        ]

        comparison_dataframe = comparison_dataframe[
            existing_columns
        ]

        comparison_dataframe = comparison_dataframe.sort_values(
            by="macro_f1_score",
            ascending=False,
        )

        comparison_path = (
            REPORT_DIR / "model_comparison.csv"
        )

        comparison_dataframe.to_csv(
            comparison_path,
            index=False,
        )

        print_section("MODEL COMPARISON")

        print(
            comparison_dataframe.to_string(
                index=False
            )
        )

        print(
            f"\nModel comparison saved: "
            f"{comparison_path}"
        )

    else:
        print(
            "\nNo model was successfully evaluated. "
            "Please check the model files and test dataset."
        )

    print_section("STEP 8 COMPLETED")

    print(f"Reports directory: {REPORT_DIR}")
    print(f"Plots directory: {PLOT_DIR}")
    print(
        f"Predictions directory: {PREDICTION_DIR}"
    )


if __name__ == "__main__":
    main()