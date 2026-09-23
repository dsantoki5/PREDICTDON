from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# STEP 5A: CREATE MACHINE HEALTH-STATUS TARGET
# ============================================================
#
# Three-class target:
#
# Healthy  -> 0
# Warning  -> 1
# Critical -> 2
#
# IMPORTANT:
# This is a rule-based target, not an independently labelled
# health-status target.
#
# Columns used to create the target must be removed from the
# model features during feature selection.
# ============================================================


# ============================================================
# 1. PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "engineered_dataset.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "health_status_dataset.csv"
)

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)


# ============================================================
# 2. CONFIGURATION
# ============================================================

FAILURE_COLUMN = "Machine_failure"

# Actual column name from the AI4I dataset
TOOL_WEAR_COLUMN = "Tool_wear_[min]"

VIBRATION_COLUMN = "vibration_level"

STATUS_COLUMN = "Machine_Status"
STATUS_CODE_COLUMN = "Machine_Status_Code"
RISK_SCORE_COLUMN = "health_risk_score"

STATUS_MAPPING = {
    "Healthy": 0,
    "Warning": 1,
    "Critical": 2,
}

# Tool-wear thresholds
TOOL_WEAR_WARNING = 150
TOOL_WEAR_CRITICAL = 200

# Vibration percentile thresholds
VIBRATION_WARNING_PERCENTILE = 75
VIBRATION_CRITICAL_PERCENTILE = 95


# ============================================================
# 3. HELPER FUNCTIONS
# ============================================================

def print_section(title: str) -> None:
    """Print a formatted section heading."""
    print("\n" + "=" * 75)
    print(title)
    print("=" * 75)


def find_tool_wear_column(dataframe: pd.DataFrame) -> str:
    """
    Find the tool-wear column.

    The original AI4I dataset normally uses:
        Tool_wear_[min]

    Some earlier project versions may use:
        Tool_wear_min
        Tool_wear_min_[min]
    """

    possible_names = [
        "Tool_wear_[min]",
        "Tool_wear_min",
        "Tool_wear_min_[min]",
        "Tool wear [min]",
    ]

    for column_name in possible_names:
        if column_name in dataframe.columns:
            return column_name

    raise ValueError(
        "\nTool-wear column was not found.\n"
        f"Expected one of: {possible_names}\n"
        f"Available columns: {dataframe.columns.tolist()}"
    )


# ============================================================
# 4. LOAD DATASET
# ============================================================

print_section("STEP 5A: MACHINE HEALTH-STATUS TARGET CREATION")

print("\nLoading engineered dataset...")
print(f"Input file: {INPUT_FILE}")

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"\nInput dataset was not found:\n{INPUT_FILE}\n\n"
        "Please run Step 4 before running this script."
    )

df = pd.read_csv(INPUT_FILE)

print(f"Input dataset shape: {df.shape}")

if df.empty:
    raise ValueError("The input dataset is empty.")


# ============================================================
# 5. DETERMINE REQUIRED COLUMNS
# ============================================================

print("\nChecking required columns...")

# Support the actual column name and compatible aliases.
resolved_tool_wear_column = find_tool_wear_column(df)

required_columns = [
    FAILURE_COLUMN,
    resolved_tool_wear_column,
    VIBRATION_COLUMN,
]

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:
    raise ValueError(
        "\nThe following required columns are missing:\n"
        f"{missing_columns}\n\n"
        f"Available columns:\n{df.columns.tolist()}"
    )

print("Required columns found:")
for column in required_columns:
    print(f"  - {column}")


# ============================================================
# 6. VALIDATE INPUT VALUES
# ============================================================

print("\nValidating input values...")

numeric_columns = [
    FAILURE_COLUMN,
    resolved_tool_wear_column,
    VIBRATION_COLUMN,
]

for column in numeric_columns:
    df[column] = pd.to_numeric(
        df[column],
        errors="coerce",
    )

missing_values = df[numeric_columns].isna().sum()

if missing_values.any():
    invalid_columns = missing_values[
        missing_values > 0
    ].to_dict()

    raise ValueError(
        "\nMissing or invalid values detected:\n"
        f"{invalid_columns}"
    )

numeric_array = df[numeric_columns].to_numpy(dtype=float)

if not np.isfinite(numeric_array).all():
    raise ValueError(
        "\nInfinite values were found in the required columns."
    )

unique_failure_values = set(
    df[FAILURE_COLUMN].unique()
)

if not unique_failure_values.issubset({0, 1}):
    raise ValueError(
        "\nMachine_failure must contain only 0 and 1.\n"
        f"Found values: {sorted(unique_failure_values)}"
    )

df[FAILURE_COLUMN] = df[FAILURE_COLUMN].astype(int)

print("Input values validated successfully.")


# ============================================================
# 7. CALCULATE VIBRATION THRESHOLDS
# ============================================================

print("\nCalculating vibration thresholds...")

vibration_warning_threshold = np.percentile(
    df[VIBRATION_COLUMN],
    75,
)

vibration_critical_threshold = np.percentile(
    df[VIBRATION_COLUMN],
    95,
)

print(
    "Vibration warning threshold "
    f"(75th percentile): {vibration_warning_threshold:.4f}"
)

print(
    "Vibration critical threshold "
    f"(95th percentile): {vibration_critical_threshold:.4f}"
)


# ============================================================
# 8. CALCULATE HEALTH-RISK SCORE
# ============================================================

print("\nCalculating health-risk scores...")

df[RISK_SCORE_COLUMN] = 0


# Tool-wear warning risk
df.loc[
    df[resolved_tool_wear_column] >= TOOL_WEAR_WARNING,
    RISK_SCORE_COLUMN,
] += 1


# Additional critical tool-wear risk
df.loc[
    df[resolved_tool_wear_column] >= TOOL_WEAR_CRITICAL,
    RISK_SCORE_COLUMN,
] += 1


# Vibration warning risk
df.loc[
    df[VIBRATION_COLUMN] >= vibration_warning_threshold,
    RISK_SCORE_COLUMN,
] += 1


# Additional critical vibration risk
df.loc[
    df[VIBRATION_COLUMN] >= vibration_critical_threshold,
    RISK_SCORE_COLUMN,
] += 1


# Observed machine failure receives two risk points
df.loc[
    df[FAILURE_COLUMN] == 1,
    RISK_SCORE_COLUMN,
] += 2


# ============================================================
# 9. CREATE THREE-CLASS TARGET
# ============================================================

print("\nCreating machine-health labels...")

# Default class
df[STATUS_COLUMN] = "Healthy"


# Warning condition
warning_condition = (
    df[RISK_SCORE_COLUMN] >= 1
)

df.loc[
    warning_condition,
    STATUS_COLUMN,
] = "Warning"


# Critical condition
#
# A machine is Critical when:
#   1. Machine_failure equals 1, or
#   2. The total risk score is at least 3.
#
# Critical is applied after Warning so that it has priority.
critical_condition = (
    (df[FAILURE_COLUMN] == 1)
    | (df[RISK_SCORE_COLUMN] >= 3)
)

df.loc[
    critical_condition,
    STATUS_COLUMN,
] = "Critical"


# Convert text labels to numerical class codes
df[STATUS_CODE_COLUMN] = (
    df[STATUS_COLUMN]
    .map(STATUS_MAPPING)
    .astype("int64")
)


# ============================================================
# 10. VALIDATE GENERATED TARGET
# ============================================================

print("\nValidating generated target...")

if df[STATUS_COLUMN].isna().any():
    raise ValueError(
        "Missing values were found in Machine_Status."
    )

valid_statuses = set(STATUS_MAPPING.keys())
generated_statuses = set(df[STATUS_COLUMN].unique())

if not generated_statuses.issubset(valid_statuses):
    raise ValueError(
        "Unexpected health-status labels were generated:\n"
        f"{generated_statuses}"
    )

valid_codes = set(STATUS_MAPPING.values())
generated_codes = set(df[STATUS_CODE_COLUMN].unique())

if not generated_codes.issubset(valid_codes):
    raise ValueError(
        "Unexpected health-status codes were generated:\n"
        f"{generated_codes}"
    )

expected_codes = df[STATUS_COLUMN].map(STATUS_MAPPING)

if not df[STATUS_CODE_COLUMN].equals(expected_codes):
    raise ValueError(
        "Machine_Status and Machine_Status_Code do not match."
    )

if not df[RISK_SCORE_COLUMN].ge(0).all():
    raise ValueError(
        "Health-risk scores cannot be negative."
    )

print("Generated target validated successfully.")


# ============================================================
# 11. DISPLAY TARGET DISTRIBUTION
# ============================================================

print_section("HEALTH-STATUS DISTRIBUTION")

status_order = [
    "Healthy",
    "Warning",
    "Critical",
]

status_counts = (
    df[STATUS_COLUMN]
    .value_counts()
    .reindex(
        status_order,
        fill_value=0,
    )
)

status_percentages = (
    status_counts / len(df) * 100
).round(2)

distribution_table = pd.DataFrame(
    {
        "Status": status_order,
        "Class_Code": [
            STATUS_MAPPING[status]
            for status in status_order
        ],
        "Count": status_counts.values,
        "Percentage": status_percentages.values,
    }
)

print(distribution_table.to_string(index=False))


# ============================================================
# 12. CLASS-BALANCE WARNINGS
# ============================================================

print("\nChecking class distribution...")

if (status_counts == 0).any():
    print(
        "\nWARNING: At least one class contains zero rows."
    )
    print(
        "Review the target-generation thresholds before "
        "continuing to model training."
    )

if len(df) >= 3 and (status_counts > 0).sum() == 3:
    smallest_class_percentage = (
        status_counts.min() / len(df) * 100
    )

    if smallest_class_percentage < 1:
        print(
            "\nWARNING: At least one class represents less "
            "than 1% of the dataset."
        )
        print(
            "Stratified model training may be affected."
        )


# ============================================================
# 13. SAVE DATASET
# ============================================================

print("\nSaving health-status dataset...")

df.to_csv(
    OUTPUT_FILE,
    index=False,
)

print(f"Output dataset shape: {df.shape}")
print(f"Saved file: {OUTPUT_FILE}")


# ============================================================
# 14. FINAL SUMMARY
# ============================================================

print_section("STEP 5A COMPLETED")

print("\nGenerated columns:")
print(f"  - {STATUS_COLUMN}")
print(f"  - {STATUS_CODE_COLUMN}")
print(f"  - {RISK_SCORE_COLUMN}")

print("\nStatus mapping:")
for status, code in STATUS_MAPPING.items():
    print(f"  {status}: {code}")

print("\nTarget-construction columns:")
print(f"  - {resolved_tool_wear_column}")
print(f"  - {VIBRATION_COLUMN}")
print(f"  - {FAILURE_COLUMN}")
print(f"  - {RISK_SCORE_COLUMN}")

print(
    "\nImportant: The target-construction columns must not be "
    "used as model features during Step 5B."
)