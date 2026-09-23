from pathlib import Path
import json
import time
import warnings

import joblib
import numpy as np
import pandas as pd

from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
)
from sklearn.ensemble import RandomForestClassifier
from lightgbm import LGBMClassifier
from xgboost import XGBClassifier

warnings.filterwarnings("ignore")


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

TRAIN_PATH = PROJECT_ROOT / "data" / "processed" / "train_dataset.csv"
TEST_PATH = PROJECT_ROOT / "data" / "processed" / "test_dataset.csv"

MODEL_DIR = PROJECT_ROOT / "models" / "tuned_models"
RESULT_DIR = PROJECT_ROOT / "results" / "tuned_models"
REPORT_DIR = PROJECT_ROOT / "reports" / "model_tuning"

RANDOM_STATE = 42
CV_FOLDS = 5
N_ITER_SEARCH = 20

TARGET_COLUMN = "Machine_Status_Code"
CLASS_LABELS = [0, 1, 2]


# ============================================================
# DIRECTORY CREATION
# ============================================================

MODEL_DIR.mkdir(parents=True, exist_ok=True)
RESULT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# DATA LOADING
# ============================================================

def load_datasets():
    print("=" * 75)
    print("STEP 7: HYPERPARAMETER TUNING")
    print("=" * 75)

    print("\nLoading datasets...")

    if not TRAIN_PATH.exists():
        raise FileNotFoundError(
            f"Training file not found: {TRAIN_PATH}"
        )

    if not TEST_PATH.exists():
        raise FileNotFoundError(
            f"Testing file not found: {TEST_PATH}"
        )

    train_df = pd.read_csv(TRAIN_PATH)
    test_df = pd.read_csv(TEST_PATH)

    print(f"Training dataset shape: {train_df.shape}")
    print(f"Testing dataset shape: {test_df.shape}")

    if TARGET_COLUMN not in train_df.columns:
        raise ValueError(
            f"Target column missing from training data: {TARGET_COLUMN}"
        )

    if TARGET_COLUMN not in test_df.columns:
        raise ValueError(
            f"Target column missing from testing data: {TARGET_COLUMN}"
        )

    return train_df, test_df


# ============================================================
# FEATURE PREPARATION
# ============================================================

def prepare_features(train_df, test_df):
    print("\n" + "=" * 75)
    print("FEATURE PREPARATION")
    print("=" * 75)

    X_train = train_df.drop(columns=[TARGET_COLUMN]).copy()
    y_train = train_df[TARGET_COLUMN].copy()

    X_test = test_df.drop(columns=[TARGET_COLUMN]).copy()
    y_test = test_df[TARGET_COLUMN].copy()

    if list(X_train.columns) != list(X_test.columns):
        raise ValueError(
            "Training and testing feature columns do not match."
        )

    # Convert Boolean columns into integers.
    boolean_columns = X_train.select_dtypes(
        include=["bool"]
    ).columns.tolist()

    for column in boolean_columns:
        X_train[column] = X_train[column].astype(int)
        X_test[column] = X_test[column].astype(int)

    # Convert categorical columns using mappings derived only from training data.
    categorical_columns = X_train.select_dtypes(
        include=["object", "category"]
    ).columns.tolist()

    for column in categorical_columns:
        train_categories = sorted(
            X_train[column]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        category_mapping = {
            value: index
            for index, value in enumerate(train_categories)
        }

        X_train[column] = (
            X_train[column]
            .astype(str)
            .map(category_mapping)
            .fillna(-1)
            .astype(int)
        )

        X_test[column] = (
            X_test[column]
            .astype(str)
            .map(category_mapping)
            .fillna(-1)
            .astype(int)
        )

    # Convert all remaining values to numeric.
    X_train = X_train.apply(pd.to_numeric, errors="coerce")
    X_test = X_test.apply(pd.to_numeric, errors="coerce")

    # Replace invalid numerical values.
    X_train = X_train.replace(
        [np.inf, -np.inf],
        np.nan
    ).fillna(0)

    X_test = X_test.replace(
        [np.inf, -np.inf],
        np.nan
    ).fillna(0)

    # Validate target values.
    y_train = pd.to_numeric(y_train, errors="raise").astype(int)
    y_test = pd.to_numeric(y_test, errors="raise").astype(int)

    train_classes = sorted(y_train.unique().tolist())
    test_classes = sorted(y_test.unique().tolist())

    if train_classes != CLASS_LABELS:
        raise ValueError(
            f"Unexpected training target classes: {train_classes}. "
            f"Expected: {CLASS_LABELS}"
        )

    if not set(test_classes).issubset(set(CLASS_LABELS)):
        raise ValueError(
            f"Unexpected testing target classes: {test_classes}. "
            f"Expected a subset of: {CLASS_LABELS}"
        )

    print(f"Training features: {X_train.shape}")
    print(f"Testing features: {X_test.shape}")
    print(f"Number of predictors: {X_train.shape[1]}")
    print(f"Training target classes: {train_classes}")
    print(f"Testing target classes: {test_classes}")

    return X_train, y_train, X_test, y_test


# ============================================================
# MODEL SEARCH SPACES
# ============================================================

def create_search_configurations():
    configurations = {}

    configurations["LightGBM"] = {
        "estimator": LGBMClassifier(
            objective="multiclass",
            num_class=3,
            random_state=RANDOM_STATE,
            n_jobs=1,
            verbosity=-1,
        ),
        "parameters": {
            "n_estimators": [100, 200, 300, 500],
            "learning_rate": [0.01, 0.03, 0.05, 0.1],
            "num_leaves": [15, 31, 50, 75],
            "max_depth": [-1, 5, 8, 12],
            "min_child_samples": [10, 20, 30, 50],
            "subsample": [0.7, 0.8, 0.9, 1.0],
            "subsample_freq": [1],
            "colsample_bytree": [0.7, 0.8, 0.9, 1.0],
            "reg_alpha": [0.0, 0.1, 0.5, 1.0],
            "reg_lambda": [0.0, 0.1, 0.5, 1.0],
        },
    }

    configurations["XGBoost"] = {
        "estimator": XGBClassifier(
            objective="multi:softprob",
            num_class=3,
            eval_metric="mlogloss",
            tree_method="hist",
            random_state=RANDOM_STATE,
            n_jobs=1,
        ),
        "parameters": {
            "n_estimators": [100, 200, 300, 500],
            "learning_rate": [0.01, 0.03, 0.05, 0.1],
            "max_depth": [3, 4, 6, 8],
            "min_child_weight": [1, 3, 5, 10],
            "subsample": [0.7, 0.8, 0.9, 1.0],
            "colsample_bytree": [0.7, 0.8, 0.9, 1.0],
            "gamma": [0, 0.1, 0.3, 0.5],
            "reg_alpha": [0.0, 0.1, 0.5, 1.0],
            "reg_lambda": [1.0, 2.0, 5.0],
        },
    }

    configurations["Random_Forest"] = {
        "estimator": RandomForestClassifier(
            random_state=RANDOM_STATE,
            n_jobs=1,
            class_weight="balanced",
        ),
        "parameters": {
            "n_estimators": [200, 300, 500],
            "max_depth": [None, 10, 20, 30],
            "min_samples_split": [2, 5, 10],
            "min_samples_leaf": [1, 2, 4],
            "max_features": ["sqrt", "log2", None],
        },
    }

    return configurations


# ============================================================
# MODEL TUNING
# ============================================================

def tune_model(
    model_name,
    estimator,
    parameters,
    X_train,
    y_train,
):
    print("\n" + "=" * 75)
    print(f"TUNING: {model_name}")
    print("=" * 75)

    cv_strategy = StratifiedKFold(
        n_splits=CV_FOLDS,
        shuffle=True,
        random_state=RANDOM_STATE,
    )

    search = RandomizedSearchCV(
        estimator=estimator,
        param_distributions=parameters,
        n_iter=N_ITER_SEARCH,
        scoring="f1_macro",
        cv=cv_strategy,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        verbose=1,
        refit=True,
        return_train_score=False,
        error_score="raise",
    )

    start_time = time.time()

    search.fit(X_train, y_train)

    elapsed_time = time.time() - start_time

    print(
        f"\nBest cross-validation Macro-F1: "
        f"{search.best_score_:.4f}"
    )

    print(f"Tuning time: {elapsed_time:.2f} seconds")

    print("\nBest parameters:")

    for parameter, value in search.best_params_.items():
        print(f" - {parameter}: {value}")

    return (
        search.best_estimator_,
        search.best_score_,
        search.best_params_,
        elapsed_time,
    )


# ============================================================
# FINAL TEST EVALUATION
# ============================================================

def evaluate_model(model_name, model, X_test, y_test):
    print("\n" + "-" * 75)
    print(f"FINAL TEST EVALUATION: {model_name}")
    print("-" * 75)

    predictions = model.predict(X_test)

    accuracy = accuracy_score(y_test, predictions)

    macro_precision = precision_score(
        y_test,
        predictions,
        labels=CLASS_LABELS,
        average="macro",
        zero_division=0,
    )

    macro_recall = recall_score(
        y_test,
        predictions,
        labels=CLASS_LABELS,
        average="macro",
        zero_division=0,
    )

    macro_f1 = f1_score(
        y_test,
        predictions,
        labels=CLASS_LABELS,
        average="macro",
        zero_division=0,
    )

    weighted_f1 = f1_score(
        y_test,
        predictions,
        labels=CLASS_LABELS,
        average="weighted",
        zero_division=0,
    )

    critical_recall = recall_score(
        y_test,
        predictions,
        labels=[2],
        average=None,
        zero_division=0,
    )[0]

    print(f"Accuracy: {accuracy:.4f}")
    print(f"Macro Precision: {macro_precision:.4f}")
    print(f"Macro Recall: {macro_recall:.4f}")
    print(f"Macro F1-score: {macro_f1:.4f}")
    print(f"Weighted F1-score: {weighted_f1:.4f}")
    print(f"Critical-class recall: {critical_recall:.4f}")

    report = classification_report(
        y_test,
        predictions,
        labels=CLASS_LABELS,
        output_dict=True,
        zero_division=0,
    )

    confusion = confusion_matrix(
        y_test,
        predictions,
        labels=CLASS_LABELS,
    )

    metrics = {
        "Model": model_name,
        "Accuracy": accuracy,
        "Macro_Precision": macro_precision,
        "Macro_Recall": macro_recall,
        "Macro_F1": macro_f1,
        "Weighted_F1": weighted_f1,
        "Critical_Class_Recall": critical_recall,
    }

    prediction_df = pd.DataFrame({
        "Actual": y_test.to_numpy(),
        "Predicted": predictions,
    })

    prediction_path = (
        RESULT_DIR / f"{model_name}_predictions.csv"
    )

    report_path = (
        REPORT_DIR / f"{model_name}_classification_report.json"
    )

    confusion_path = (
        RESULT_DIR / f"{model_name}_confusion_matrix.csv"
    )

    prediction_df.to_csv(
        prediction_path,
        index=False,
    )

    pd.DataFrame(report).transpose().to_json(
        report_path,
        indent=4,
    )

    pd.DataFrame(
        confusion,
        index=[f"Actual_{label}" for label in CLASS_LABELS],
        columns=[f"Predicted_{label}" for label in CLASS_LABELS],
    ).to_csv(confusion_path)

    return metrics


# ============================================================
# MAIN EXECUTION
# ============================================================

def main():
    train_df, test_df = load_datasets()

    X_train, y_train, X_test, y_test = prepare_features(
        train_df,
        test_df,
    )

    configurations = create_search_configurations()

    all_results = []
    tuning_configuration = {}

    for model_name, configuration in configurations.items():
        (
            best_model,
            best_cv_score,
            best_params,
            tuning_time,
        ) = tune_model(
            model_name=model_name,
            estimator=configuration["estimator"],
            parameters=configuration["parameters"],
            X_train=X_train,
            y_train=y_train,
        )

        metrics = evaluate_model(
            model_name=model_name,
            model=best_model,
            X_test=X_test,
            y_test=y_test,
        )

        metrics["Best_CV_Macro_F1"] = best_cv_score
        metrics["Tuning_Time_Seconds"] = tuning_time

        all_results.append(metrics)

        model_path = MODEL_DIR / f"{model_name}.joblib"
        joblib.dump(best_model, model_path)

        tuning_configuration[model_name] = {
            "best_parameters": best_params,
            "best_cv_macro_f1": best_cv_score,
            "model_path": str(model_path),
        }

        print(f"\nSaved tuned model: {model_path}")

    results_df = pd.DataFrame(all_results)

    # Macro-F1 is the primary selection metric because the
    # project contains three classes with unequal distributions.
    results_df = results_df.sort_values(
        by="Macro_F1",
        ascending=False,
    )

    results_path = RESULT_DIR / "tuned_model_metrics.csv"
    configuration_path = REPORT_DIR / "tuning_configuration.json"

    results_df.to_csv(
        results_path,
        index=False,
    )

    with open(
        configuration_path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            tuning_configuration,
            file,
            indent=4,
            default=str,
        )

    print("\n" + "=" * 75)
    print("STEP 7 COMPLETED SUCCESSFULLY")
    print("=" * 75)

    print("\nTuned model performance summary:")
    print(results_df.to_string(index=False))

    print("\nSaved results:")
    print(f" - {results_path}")
    print(f" - {configuration_path}")


if __name__ == "__main__":
    main()