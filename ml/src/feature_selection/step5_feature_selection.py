from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "health_status_dataset.csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

TRAIN_OUTPUT = OUTPUT_DIR / "train_dataset.csv"
TEST_OUTPUT = OUTPUT_DIR / "test_dataset.csv"
COMBINED_OUTPUT = OUTPUT_DIR / "model_ready_dataset.csv"
FEATURE_LIST_OUTPUT = OUTPUT_DIR / "all_features.txt"


# ============================================================
# CONFIGURATION
# ============================================================

TARGET_COLUMN = "Machine_Status_Code"
STATUS_COLUMN = "Machine_Status"

TEST_SIZE = 0.20
RANDOM_STATE = 42


# ============================================================
# COLUMNS THAT MUST NOT BE USED AS MODEL FEATURES
# ============================================================

EXCLUDED_COLUMNS = {
    # Identifiers
    "UDI",
    "Product_ID",
    "Product_ID_encoded",

    # Target columns
    "Machine_Status",
    "Machine_Status_Code",

    # Columns used to construct the rule-based target
    "Machine_failure",
    "health_risk_score",

    # Original tool-wear column and possible naming variants
    "Tool_wear_min",
    "Tool_wear_[min]",
    "Tool_wear",
    "Tool_wear_min_rolling_mean",
    "Tool_wear_min_rolling_std",
    "Tool_wear_min_rolling_min",
    "Tool_wear_min_rolling_max",
    "Tool_wear_min_change",
    "Tool_wear_min_diff",
    "tool_wear_change",
    "tool_wear_mean_10",

    # Vibration-related target construction features
    "vibration_level",
    "vibration_stress",

    # Failure-mode indicators
    "TWF",
    "HDF",
    "PWF",
    "OSF",
    "RNF",
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def convert_boolean_columns_to_integer(dataframe):
    """
    Convert Boolean columns into integer columns.
    """
    dataframe = dataframe.copy()

    boolean_columns = dataframe.select_dtypes(
        include=["bool"]
    ).columns

    for column in boolean_columns:
        dataframe[column] = dataframe[column].astype(int)

    return dataframe


def prepare_features(train_features, test_features):
    """
    Prepare train and test features consistently.

    Processing steps:
    1. Convert Boolean columns to integers.
    2. One-hot encode categorical columns.
    3. Align test columns with training columns.
    4. Replace infinite values with NaN.
    5. Calculate missing-value replacements using training data only.
    6. Apply the same replacements to the test data.
    """

    train_features = convert_boolean_columns_to_integer(train_features)
    test_features = convert_boolean_columns_to_integer(test_features)

    train_features = pd.get_dummies(
        train_features,
        drop_first=True
    )

    test_features = pd.get_dummies(
        test_features,
        drop_first=True
    )

    # Ensure both datasets have exactly the same columns.
    test_features = test_features.reindex(
        columns=train_features.columns,
        fill_value=0
    )

    # Replace infinite values.
    train_features = train_features.replace(
        [np.inf, -np.inf],
        np.nan
    )

    test_features = test_features.replace(
        [np.inf, -np.inf],
        np.nan
    )

    # Convert all columns to numeric values.
    train_features = train_features.apply(
        pd.to_numeric,
        errors="coerce"
    )

    test_features = test_features.apply(
        pd.to_numeric,
        errors="coerce"
    )

    # Calculate imputation values from training data only.
    training_medians = train_features.median()

    train_features = train_features.fillna(training_medians)
    test_features = test_features.fillna(training_medians)

    # Handle columns that are completely empty in the training set.
    train_features = train_features.fillna(0)
    test_features = test_features.fillna(0)

    # Ensure consistent numeric data types.
    train_features = train_features.astype(float)
    test_features = test_features.astype(float)

    return train_features, test_features


# ============================================================
# MAIN PROCESSING PIPELINE
# ============================================================

def main():
    print("=" * 70)
    print("STEP 5B - FEATURE PREPARATION")
    print("=" * 70)

    # --------------------------------------------------------
    # 1. Check input file
    # --------------------------------------------------------

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file was not found:\n{INPUT_FILE}"
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # 2. Load the health-status dataset
    # --------------------------------------------------------

    dataframe = pd.read_csv(INPUT_FILE)

    print(f"\nInput file: {INPUT_FILE}")
    print(f"Input dataset shape: {dataframe.shape}")

    required_columns = {
        TARGET_COLUMN,
        STATUS_COLUMN
    }

    missing_required_columns = required_columns - set(
        dataframe.columns
    )

    if missing_required_columns:
        raise ValueError(
            "The following required columns are missing: "
            f"{sorted(missing_required_columns)}"
        )

    # --------------------------------------------------------
    # 3. Validate target values
    # --------------------------------------------------------

    target_values = set(
        dataframe[TARGET_COLUMN].dropna().unique()
    )

    expected_target_values = {0, 1, 2}

    if not target_values.issubset(expected_target_values):
        raise ValueError(
            "Unexpected target values found in "
            f"{TARGET_COLUMN}: {sorted(target_values)}"
        )

    if dataframe[TARGET_COLUMN].isna().any():
        raise ValueError(
            f"Missing values found in target column: {TARGET_COLUMN}"
        )

    # Verify that the status-code mapping is consistent.
    expected_status_mapping = {
        0: "Healthy",
        1: "Warning",
        2: "Critical",
    }

    for code, expected_status in expected_status_mapping.items():
        observed_statuses = set(
            dataframe.loc[
                dataframe[TARGET_COLUMN] == code,
                STATUS_COLUMN
            ].dropna().astype(str)
        )

        if observed_statuses and observed_statuses != {expected_status}:
            raise ValueError(
                f"Inconsistent status mapping for code {code}. "
                f"Expected '{expected_status}', found "
                f"{sorted(observed_statuses)}"
            )

    print("\nTarget distribution:")
    print(dataframe[STATUS_COLUMN].value_counts())

    # --------------------------------------------------------
    # 4. Separate features and target
    # --------------------------------------------------------

    columns_to_exclude = set(EXCLUDED_COLUMNS)

    actual_excluded_columns = [
        column
        for column in dataframe.columns
        if column in columns_to_exclude
    ]

    feature_columns = [
        column
        for column in dataframe.columns
        if column not in columns_to_exclude
    ]

    if not feature_columns:
        raise ValueError(
            "No usable feature columns remain after exclusions."
        )

    features = dataframe[feature_columns].copy()
    target = dataframe[TARGET_COLUMN].copy()

    # Check for duplicate feature names.
    if features.columns.duplicated().any():
        duplicate_columns = features.columns[
            features.columns.duplicated()
        ].tolist()

        raise ValueError(
            f"Duplicate feature columns detected: {duplicate_columns}"
        )

    # Final leakage check.
    remaining_leakage_columns = [
        column
        for column in features.columns
        if column in columns_to_exclude
        or "Machine_Status" in column
        or "health_risk_score" in column
    ]

    if remaining_leakage_columns:
        raise ValueError(
            "Potential leakage columns remain in the feature set: "
            f"{remaining_leakage_columns}"
        )

    print(
        f"\nExcluded columns found in dataset: "
        f"{len(actual_excluded_columns)}"
    )

    print(
        f"Features retained before encoding: "
        f"{len(feature_columns)}"
    )

    # --------------------------------------------------------
    # 5. Split before imputation and feature preparation
    # --------------------------------------------------------

    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        features,
        target,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=target
    )

    print("\nDataset split:")
    print(f"Training samples: {len(X_train_raw)}")
    print(f"Testing samples: {len(X_test_raw)}")

    # --------------------------------------------------------
    # 6. Prepare the feature matrices
    # --------------------------------------------------------

    X_train, X_test = prepare_features(
        X_train_raw,
        X_test_raw
    )

    print(
        f"\nFeatures retained after encoding: "
        f"{X_train.shape[1]}"
    )

    # --------------------------------------------------------
    # 7. Construct train and test datasets
    # --------------------------------------------------------

    train_dataset = X_train.copy()
    train_dataset[TARGET_COLUMN] = y_train.to_numpy()

    test_dataset = X_test.copy()
    test_dataset[TARGET_COLUMN] = y_test.to_numpy()

    # Reset indexes for clean CSV output.
    train_dataset = train_dataset.reset_index(drop=True)
    test_dataset = test_dataset.reset_index(drop=True)

    # --------------------------------------------------------
    # 8. Save train and test datasets
    # --------------------------------------------------------

    train_dataset.to_csv(
        TRAIN_OUTPUT,
        index=False
    )

    test_dataset.to_csv(
        TEST_OUTPUT,
        index=False
    )

    # --------------------------------------------------------
    # 9. Save a combined reference dataset
    # --------------------------------------------------------

    combined_train = train_dataset.copy()
    combined_train["Dataset_Split"] = "train"

    combined_test = test_dataset.copy()
    combined_test["Dataset_Split"] = "test"

    combined_dataset = pd.concat(
        [combined_train, combined_test],
        ignore_index=True
    )

    combined_dataset.to_csv(
        COMBINED_OUTPUT,
        index=False
    )

    # --------------------------------------------------------
    # 10. Save the complete feature list
    # --------------------------------------------------------

    with open(FEATURE_LIST_OUTPUT, "w", encoding="utf-8") as file:
        for feature_name in X_train.columns:
            file.write(f"{feature_name}\n")

    # --------------------------------------------------------
    # 11. Display final information
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("STEP 5B COMPLETED SUCCESSFULLY")
    print("=" * 70)

    print(f"\nFinal training dataset shape: {train_dataset.shape}")
    print(f"Final testing dataset shape: {test_dataset.shape}")
    print(f"Final combined dataset shape: {combined_dataset.shape}")

    print("\nSaved files:")
    print(f"1. {TRAIN_OUTPUT}")
    print(f"2. {TEST_OUTPUT}")
    print(f"3. {COMBINED_OUTPUT}")
    print(f"4. {FEATURE_LIST_OUTPUT}")

    print("\nFinal feature columns:")
    for index, feature_name in enumerate(X_train.columns, start=1):
        print(f"{index}. {feature_name}")

    print("\nTarget column:")
    print(TARGET_COLUMN)

    print("\nNo correlation-based feature reduction was applied.")
    print("All retained features will be available for model training.")


# ============================================================
# SCRIPT ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()