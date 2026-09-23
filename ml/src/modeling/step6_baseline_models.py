from pathlib import Path
import json
import time
import warnings

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC

from lightgbm import LGBMClassifier
from xgboost import XGBClassifier


warnings.filterwarnings("ignore")


# ============================================================
# 1. PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data" / "processed"

TRAIN_FILE = DATA_DIR / "train_dataset.csv"
TEST_FILE = DATA_DIR / "test_dataset.csv"

MODEL_DIR = PROJECT_ROOT / "models" / "baseline_models"
RESULTS_DIR = PROJECT_ROOT / "results" / "baseline_models"
PREDICTIONS_DIR = RESULTS_DIR / "predictions"
CONFUSION_MATRIX_DIR = RESULTS_DIR / "confusion_matrices"
REPORT_DIR = PROJECT_ROOT / "reports" / "model_training"

for directory in [
    MODEL_DIR,
    RESULTS_DIR,
    PREDICTIONS_DIR,
    CONFUSION_MATRIX_DIR,
    REPORT_DIR,
]:
    directory.mkdir(
        parents=True,
        exist_ok=True,
    )


# ============================================================
# 2. CONFIGURATION
# ============================================================

TARGET_COLUMN = "Machine_Status_Code"

RANDOM_STATE = 42

EXPECTED_TRAIN_ROWS = 8000
EXPECTED_TEST_ROWS = 2000

EXPECTED_CLASSES = [0, 1, 2]

CLASS_NAMES = {
    0: "Healthy",
    1: "Warning",
    2: "Critical",
}


# ============================================================
# 3. HELPER FUNCTIONS
# ============================================================

def print_section(title):
    """Print a formatted section heading."""

    print("\n" + "=" * 75)
    print(title)
    print("=" * 75)


def validate_dataset(dataset, dataset_name):
    """Validate the structure and target values of a dataset."""

    if dataset.empty:
        raise ValueError(
            f"{dataset_name} dataset is empty."
        )

    if TARGET_COLUMN not in dataset.columns:
        raise ValueError(
            f"{TARGET_COLUMN} is missing from "
            f"{dataset_name} dataset."
        )

    if dataset.columns.duplicated().any():
        duplicate_columns = dataset.columns[
            dataset.columns.duplicated()
        ].tolist()

        raise ValueError(
            f"{dataset_name} dataset contains duplicate "
            f"columns: {duplicate_columns}"
        )

    if dataset[TARGET_COLUMN].isnull().any():
        raise ValueError(
            f"{dataset_name} target contains missing values."
        )

    invalid_labels = set(
        dataset[TARGET_COLUMN].unique()
    ) - set(EXPECTED_CLASSES)

    if invalid_labels:
        raise ValueError(
            f"Unexpected target labels in {dataset_name}: "
            f"{sorted(invalid_labels)}"
        )

    if dataset[TARGET_COLUMN].nunique() < 2:
        raise ValueError(
            f"{dataset_name} dataset contains fewer than "
            "two target classes."
        )


def prepare_features(train_dataset, test_dataset):
    """
    Prepare training and testing features.

    Step 5B already performs feature preparation, so this function
    primarily validates the data and ensures that both datasets
    have matching numeric feature columns.
    """

    X_train = train_dataset.drop(
        columns=[TARGET_COLUMN]
    ).copy()

    y_train = train_dataset[TARGET_COLUMN].copy()

    X_test = test_dataset.drop(
        columns=[TARGET_COLUMN]
    ).copy()

    y_test = test_dataset[TARGET_COLUMN].copy()

    # Ensure that train and test have exactly the same columns.
    if set(X_train.columns) != set(X_test.columns):
        train_only = sorted(
            set(X_train.columns) - set(X_test.columns)
        )

        test_only = sorted(
            set(X_test.columns) - set(X_train.columns)
        )

        raise ValueError(
            "Train and test feature columns do not match.\n"
            f"Train-only columns: {train_only}\n"
            f"Test-only columns: {test_only}"
        )

    # Match test-column order with training-column order.
    X_test = X_test[X_train.columns]

    # Convert Boolean columns to integers if any exist.
    boolean_columns = X_train.select_dtypes(
        include=["bool"]
    ).columns.tolist()

    for column in boolean_columns:
        X_train[column] = X_train[column].astype(int)
        X_test[column] = X_test[column].astype(int)

    # Convert all feature values to numeric values.
    for column in X_train.columns:
        X_train[column] = pd.to_numeric(
            X_train[column],
            errors="coerce",
        )

        X_test[column] = pd.to_numeric(
            X_test[column],
            errors="coerce",
        )

    # Replace infinite values with missing values.
    X_train = X_train.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    X_test = X_test.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    if X_train.shape[1] == 0:
        raise ValueError(
            "No predictor columns remain after preprocessing."
        )

    # Check for obvious leakage-related columns.
    forbidden_columns = {
        "UDI",
        "Product_ID",
        "Product_ID_encoded",
        "Machine_failure",
        "Machine_Status",
        "Machine_Status_Code",
        "health_risk_score",
        "Tool_wear_min",
        "Tool_wear_[min]",
        "Tool_wear_min_change",
        "Tool_wear_min_diff",
        "tool_wear_change",
        "vibration_level",
        "vibration_stress",
        "TWF",
        "HDF",
        "PWF",
        "OSF",
        "RNF",
    }

    leakage_columns = [
        column
        for column in X_train.columns
        if column in forbidden_columns
        or "Machine_Status" in column
        or "health_risk_score" in column
    ]

    if leakage_columns:
        raise ValueError(
            "Potential leakage columns found in the training "
            f"features: {leakage_columns}"
        )

    return X_train, y_train, X_test, y_test


def build_model_pipelines():
    """Build the five baseline classification pipelines."""

    numeric_preprocessor = Pipeline(
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

    tree_preprocessor = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(strategy="median"),
            ),
        ]
    )

    models = {
        "Logistic_Regression": Pipeline(
            steps=[
                (
                    "preprocessing",
                    numeric_preprocessor,
                ),
                (
                    "classifier",
                    LogisticRegression(
                        max_iter=2000,
                        class_weight="balanced",
                        random_state=RANDOM_STATE,
                    ),
                ),
            ]
        ),

        "Decision_Tree": Pipeline(
            steps=[
                (
                    "preprocessing",
                    tree_preprocessor,
                ),
                (
                    "classifier",
                    DecisionTreeClassifier(
                        class_weight="balanced",
                        random_state=RANDOM_STATE,
                    ),
                ),
            ]
        ),

        "Random_Forest": Pipeline(
            steps=[
                (
                    "preprocessing",
                    tree_preprocessor,
                ),
                (
                    "classifier",
                    RandomForestClassifier(
                        n_estimators=300,
                        class_weight="balanced",
                        random_state=RANDOM_STATE,
                        n_jobs=-1,
                    ),
                ),
            ]
        ),

        "LightGBM": Pipeline(
            steps=[
                (
                    "preprocessing",
                    tree_preprocessor,
                ),
                (
                    "classifier",
                    LGBMClassifier(
                        objective="multiclass",
                        num_class=3,
                        n_estimators=200,
                        learning_rate=0.05,
                        num_leaves=31,
                        max_depth=-1,
                        class_weight="balanced",
                        random_state=RANDOM_STATE,
                        n_jobs=-1,
                        verbosity=-1,
                    ),
                ),
            ]
        ),

        "XGBoost": Pipeline(
            steps=[
                (
                    "preprocessing",
                    tree_preprocessor,
                ),
                (
                    "classifier",
                    XGBClassifier(
                        objective="multi:softprob",
                        num_class=3,
                        n_estimators=200,
                        learning_rate=0.05,
                        max_depth=6,
                        subsample=0.8,
                        colsample_bytree=0.8,
                        eval_metric="mlogloss",
                        tree_method="hist",
                        random_state=RANDOM_STATE,
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
    }

    return models


def calculate_metrics(y_true, y_pred):
    """Calculate the main multiclass evaluation metrics."""

    return {
        "Accuracy": accuracy_score(
            y_true,
            y_pred,
        ),

        "Macro_Precision": precision_score(
            y_true,
            y_pred,
            labels=EXPECTED_CLASSES,
            average="macro",
            zero_division=0,
        ),

        "Macro_Recall": recall_score(
            y_true,
            y_pred,
            labels=EXPECTED_CLASSES,
            average="macro",
            zero_division=0,
        ),

        "Macro_F1": f1_score(
            y_true,
            y_pred,
            labels=EXPECTED_CLASSES,
            average="macro",
            zero_division=0,
        ),

        "Weighted_F1": f1_score(
            y_true,
            y_pred,
            labels=EXPECTED_CLASSES,
            average="weighted",
            zero_division=0,
        ),

        "Critical_Class_Recall": recall_score(
            y_true,
            y_pred,
            labels=[2],
            average="macro",
            zero_division=0,
        ),
    }


def create_confusion_matrix_plot(
    actual,
    predicted,
    model_name,
    output_path,
):
    """Create and save a confusion-matrix plot."""

    matrix = confusion_matrix(
        actual,
        predicted,
        labels=EXPECTED_CLASSES,
    )

    display_labels = [
        CLASS_NAMES[label]
        for label in EXPECTED_CLASSES
    ]

    figure, axis = plt.subplots(
        figsize=(7, 6)
    )

    image = axis.imshow(matrix)

    axis.set_title(
        f"Confusion Matrix - {model_name}"
    )

    axis.set_xlabel("Predicted Class")
    axis.set_ylabel("Actual Class")

    axis.set_xticks(
        range(len(display_labels))
    )

    axis.set_yticks(
        range(len(display_labels))
    )

    axis.set_xticklabels(display_labels)
    axis.set_yticklabels(display_labels)

    for row_index in range(matrix.shape[0]):
        for column_index in range(matrix.shape[1]):
            axis.text(
                column_index,
                row_index,
                str(matrix[row_index, column_index]),
                ha="center",
                va="center",
            )

    figure.colorbar(
        image,
        ax=axis,
    )

    figure.tight_layout()

    figure.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close(figure)


# ============================================================
# 4. LOAD DATASETS
# ============================================================

print_section("STEP 6: BASELINE MODEL TRAINING")

print("\nLoading datasets...")

if not TRAIN_FILE.exists():
    raise FileNotFoundError(
        f"Training file not found: {TRAIN_FILE}"
    )

if not TEST_FILE.exists():
    raise FileNotFoundError(
        f"Testing file not found: {TEST_FILE}"
    )

train_dataset = pd.read_csv(TRAIN_FILE)
test_dataset = pd.read_csv(TEST_FILE)

print(
    f"Training dataset shape: {train_dataset.shape}"
)

print(
    f"Testing dataset shape: {test_dataset.shape}"
)


# ============================================================
# 5. DATASET VALIDATION
# ============================================================

print_section("DATASET VALIDATION")

validate_dataset(
    train_dataset,
    "training",
)

validate_dataset(
    test_dataset,
    "testing",
)

if len(train_dataset) != EXPECTED_TRAIN_ROWS:
    raise ValueError(
        "Unexpected training-row count. "
        f"Expected {EXPECTED_TRAIN_ROWS}, "
        f"received {len(train_dataset)}."
    )

if len(test_dataset) != EXPECTED_TEST_ROWS:
    raise ValueError(
        "Unexpected testing-row count. "
        f"Expected {EXPECTED_TEST_ROWS}, "
        f"received {len(test_dataset)}."
    )

print("Dataset validation passed.")


# ============================================================
# 6. PREPARE FEATURES AND TARGET
# ============================================================

print_section("FEATURE PREPARATION")

X_train, y_train, X_test, y_test = prepare_features(
    train_dataset,
    test_dataset,
)

print(
    f"Training features: {X_train.shape}"
)

print(
    f"Testing features: {X_test.shape}"
)

print(
    f"Number of predictors: {X_train.shape[1]}"
)

print("Feature preparation passed.")


# ============================================================
# 7. BUILD MODELS
# ============================================================

models = build_model_pipelines()

print_section("MODELS TO BE TRAINED")

for model_name in models:
    print(f" - {model_name}")

print(
    f"\nTotal models: {len(models)}"
)


# ============================================================
# 8. TRAIN AND EVALUATE MODELS
# ============================================================

all_metrics = []
all_classification_reports = []

for model_name, model_pipeline in models.items():

    print_section(
        f"TRAINING: {model_name}"
    )

    start_time = time.perf_counter()

    model_pipeline.fit(
        X_train,
        y_train,
    )

    training_time = (
        time.perf_counter() - start_time
    )

    prediction_start_time = time.perf_counter()

    y_pred = model_pipeline.predict(
        X_test
    )

    prediction_time = (
        time.perf_counter() - prediction_start_time
    )

    metrics = calculate_metrics(
        y_test,
        y_pred,
    )

    # Generate the detailed classification report.
    report_dictionary = classification_report(
        y_test,
        y_pred,
        labels=EXPECTED_CLASSES,
        target_names=[
            CLASS_NAMES[label]
            for label in EXPECTED_CLASSES
        ],
        output_dict=True,
        zero_division=0,
    )

    report_dataframe = pd.DataFrame(
        report_dictionary
    ).transpose()

    report_path = (
        REPORT_DIR
        / f"{model_name}_classification_report.csv"
    )

    report_dataframe.to_csv(
        report_path
    )

    # Save predictions.
    prediction_dataframe = pd.DataFrame({
        "Actual_Status_Code": y_test.to_numpy(),
        "Predicted_Status_Code": y_pred,
        "Actual_Status": [
            CLASS_NAMES.get(
                int(value),
                "Unknown",
            )
            for value in y_test
        ],
        "Predicted_Status": [
            CLASS_NAMES.get(
                int(value),
                "Unknown",
            )
            for value in y_pred
        ],
    })

    prediction_path = (
        PREDICTIONS_DIR
        / f"{model_name}_predictions.csv"
    )

    prediction_dataframe.to_csv(
        prediction_path,
        index=False,
    )

    # Save the confusion matrix.
    confusion_matrix_path = (
        CONFUSION_MATRIX_DIR
        / f"{model_name}_confusion_matrix.png"
    )

    create_confusion_matrix_plot(
        actual=y_test,
        predicted=y_pred,
        model_name=model_name.replace("_", " "),
        output_path=confusion_matrix_path,
    )

    # Save the trained model.
    model_path = (
        MODEL_DIR
        / f"{model_name}.joblib"
    )

    joblib.dump(
        model_pipeline,
        model_path,
    )

    # Store metrics.
    model_metrics = {
        "Model": model_name,
        **metrics,
        "Training_Time_Seconds": training_time,
        "Prediction_Time_Seconds": prediction_time,
        "Number_of_Training_Rows": len(X_train),
        "Number_of_Testing_Rows": len(X_test),
        "Number_of_Predictors": X_train.shape[1],
    }

    all_metrics.append(
        model_metrics
    )

    # Store class-level report rows.
    for class_name, class_metrics in report_dictionary.items():

        if isinstance(class_metrics, dict):
            all_classification_reports.append({
                "Model": model_name,
                "Class": class_name,
                **class_metrics,
            })

    print(
        f"\nAccuracy: {metrics['Accuracy']:.4f}"
    )

    print(
        f"Macro Precision: "
        f"{metrics['Macro_Precision']:.4f}"
    )

    print(
        f"Macro Recall: "
        f"{metrics['Macro_Recall']:.4f}"
    )

    print(
        f"Macro F1-score: "
        f"{metrics['Macro_F1']:.4f}"
    )

    print(
        f"Weighted F1-score: "
        f"{metrics['Weighted_F1']:.4f}"
    )

    print(
        f"Critical-class recall: "
        f"{metrics['Critical_Class_Recall']:.4f}"
    )

    print(
        f"Training time: "
        f"{training_time:.4f} seconds"
    )

    print(
        f"Prediction time: "
        f"{prediction_time:.4f} seconds"
    )

    print("\nSaved:")
    print(f" - Model: {model_path}")
    print(f" - Predictions: {prediction_path}")
    print(f" - Confusion matrix: {confusion_matrix_path}")
    print(f" - Classification report: {report_path}")


# ============================================================
# 9. SAVE COMBINED RESULTS
# ============================================================

print_section("SAVING COMBINED RESULTS")

metrics_dataframe = pd.DataFrame(
    all_metrics
)

metrics_dataframe = metrics_dataframe.sort_values(
    by="Macro_F1",
    ascending=False,
).reset_index(drop=True)

metrics_path = (
    RESULTS_DIR / "baseline_metrics.csv"
)

metrics_dataframe.to_csv(
    metrics_path,
    index=False,
)

classification_reports_dataframe = pd.DataFrame(
    all_classification_reports
)

classification_reports_path = (
    RESULTS_DIR / "all_classification_reports.csv"
)

classification_reports_dataframe.to_csv(
    classification_reports_path,
    index=False,
)

# Save the feature list used by the models.
feature_list_path = (
    REPORT_DIR / "training_features.txt"
)

with open(
    feature_list_path,
    "w",
    encoding="utf-8",
) as feature_file:

    for feature in X_train.columns:
        feature_file.write(
            f"{feature}\n"
        )

# Save the training configuration.
configuration = {
    "target_column": TARGET_COLUMN,
    "random_state": RANDOM_STATE,
    "expected_classes": EXPECTED_CLASSES,
    "class_names": CLASS_NAMES,
    "training_file": str(TRAIN_FILE),
    "testing_file": str(TEST_FILE),
    "training_rows": len(X_train),
    "testing_rows": len(X_test),
    "number_of_predictors": X_train.shape[1],
    "models_trained": list(models.keys()),
}

configuration_path = (
    REPORT_DIR / "training_configuration.json"
)

with open(
    configuration_path,
    "w",
    encoding="utf-8",
) as configuration_file:

    json.dump(
        configuration,
        configuration_file,
        indent=4,
    )


# ============================================================
# 10. FINAL SUMMARY
# ============================================================

print_section("STEP 6 COMPLETED SUCCESSFULLY")

print("\nModel performance summary:")

print(
    metrics_dataframe[
        [
            "Model",
            "Accuracy",
            "Macro_F1",
            "Critical_Class_Recall",
        ]
    ].to_string(index=False)
)

print("\nSaved result files:")
print(f" - {metrics_path}")
print(f" - {classification_reports_path}")
print(f" - {feature_list_path}")
print(f" - {configuration_path}")

print("\nModels trained:")

for model_name in models:
    print(f" - {model_name}")

print("\nAll five baseline models were trained and evaluated.")