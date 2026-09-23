from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "cleaned_dataset.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "signal_features.csv"
)

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# CONFIGURATION
# ============================================================

TARGET_COLUMN = "Machine_failure"
WINDOW_SIZE = 10

SENSOR_COLUMNS = [
    "Air_temperature_K",
    "Process_temperature_K",
    "Rotational_speed_rpm",
    "Torque_Nm",
    "Tool_wear_min"
]


# ============================================================
# 1. LOAD CLEANED DATASET
# ============================================================

print("\nLoading cleaned dataset...")

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Input file not found:\n{INPUT_FILE}"
    )

df = pd.read_csv(INPUT_FILE)

print("Original input shape:", df.shape)

print("\nOriginal columns:")
print(df.columns.tolist())


# ============================================================
# 2. STANDARDIZE COLUMN NAMES
# ============================================================

def standardize_column_name(column_name):
    """
    Converts column names into the project's standard format.
    """

    return (
        str(column_name)
        .strip()
        .replace("[", "")
        .replace("]", "")
        .replace("(", "")
        .replace(")", "")
        .replace(" ", "_")
        .replace("/", "_")
    )


df.columns = [
    standardize_column_name(column)
    for column in df.columns
]

# Check for duplicate column names after standardization.
if df.columns.duplicated().any():
    duplicate_columns = df.columns[
        df.columns.duplicated()
    ].tolist()

    raise ValueError(
        "Duplicate column names found after standardization: "
        f"{duplicate_columns}"
    )

print("\nStandardized columns:")
print(df.columns.tolist())


# ============================================================
# 3. VALIDATE REQUIRED COLUMNS
# ============================================================

required_columns = [
    "UDI",
    TARGET_COLUMN,
    *SENSOR_COLUMNS
]

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:
    raise ValueError(
        "The following required columns are missing: "
        f"{missing_columns}"
    )


# ============================================================
# 4. VALIDATE RECORD IDENTIFIERS
# ============================================================

# The AI4I dataset does not contain a genuine timestamp or
# machine-specific chronological sequence.
#
# Therefore, the original row order is preserved.
# Rolling features are row-order proxy features only.

if df["UDI"].isnull().any():
    raise ValueError(
        "UDI contains missing values."
    )

if df["UDI"].duplicated().any():
    raise ValueError(
        "Duplicate UDI values were found."
    )

# Preserve the original row order.
df = df.reset_index(drop=True)


# ============================================================
# 5. VALIDATE SENSOR DATA TYPES
# ============================================================

for column in SENSOR_COLUMNS:

    original_values = df[column].copy()

    converted_values = pd.to_numeric(
        original_values,
        errors="coerce"
    )

    if converted_values.isnull().any():
        invalid_count = int(
            converted_values.isnull().sum()
        )

        raise ValueError(
            f"Column '{column}' contains "
            f"{invalid_count} non-numeric or missing values."
        )

    df[column] = converted_values


# ============================================================
# 6. VALIDATE TARGET COLUMN
# ============================================================

target_values = pd.to_numeric(
    df[TARGET_COLUMN],
    errors="coerce"
)

if target_values.isnull().any():
    raise ValueError(
        f"Target column '{TARGET_COLUMN}' contains "
        "invalid or missing values."
    )

df[TARGET_COLUMN] = target_values

if not set(df[TARGET_COLUMN].unique()).issubset({0, 1}):
    raise ValueError(
        f"Target column '{TARGET_COLUMN}' must contain "
        "only 0 and 1."
    )


# ============================================================
# 7. CREATE SIGNAL FEATURES
# ============================================================

print("\nGenerating signal features...")

feature_data = pd.DataFrame(
    index=df.index
)

for column in SENSOR_COLUMNS:

    series = df[column]

    # --------------------------------------------------------
    # Rolling mean
    # --------------------------------------------------------

    feature_data[
        f"{column}_rolling_mean"
    ] = (
        series
        .rolling(
            window=WINDOW_SIZE,
            min_periods=1
        )
        .mean()
    )

    # --------------------------------------------------------
    # Rolling standard deviation
    # --------------------------------------------------------

    feature_data[
        f"{column}_rolling_std"
    ] = (
        series
        .rolling(
            window=WINDOW_SIZE,
            min_periods=1
        )
        .std()
        .fillna(0)
    )

    # --------------------------------------------------------
    # Rolling minimum
    # --------------------------------------------------------

    feature_data[
        f"{column}_rolling_min"
    ] = (
        series
        .rolling(
            window=WINDOW_SIZE,
            min_periods=1
        )
        .min()
    )

    # --------------------------------------------------------
    # Rolling maximum
    # --------------------------------------------------------

    feature_data[
        f"{column}_rolling_max"
    ] = (
        series
        .rolling(
            window=WINDOW_SIZE,
            min_periods=1
        )
        .max()
    )

    # --------------------------------------------------------
    # Change from previous row
    # --------------------------------------------------------

    feature_data[
        f"{column}_change"
    ] = (
        series
        .diff()
        .fillna(0)
    )


# ============================================================
# 8. CREATE DOMAIN-SPECIFIC FEATURES
# ============================================================

# ------------------------------------------------------------
# Temperature difference
# ------------------------------------------------------------

feature_data["temperature_difference"] = (
    df["Process_temperature_K"]
    - df["Air_temperature_K"]
)


# ------------------------------------------------------------
# Mechanical power approximation
# ------------------------------------------------------------
#
# Power = 2 * pi * rotational_speed * torque / 60
#
# Rotational speed is measured in RPM.
# Torque is measured in Nm.
# The resulting value is an approximate mechanical power
# in watts.
# ------------------------------------------------------------

feature_data["power_consumption"] = (
    2
    * np.pi
    * df["Rotational_speed_rpm"]
    * df["Torque_Nm"]
    / 60
)


# ------------------------------------------------------------
# Load-related signal
# ------------------------------------------------------------

feature_data["load_signal"] = (
    df["Rotational_speed_rpm"]
    * df["Torque_Nm"]
)


# ------------------------------------------------------------
# Tool-wear change
# ------------------------------------------------------------

feature_data["tool_wear_change"] = (
    df["Tool_wear_min"]
    .diff()
    .fillna(0)
)


# ============================================================
# 9. VALIDATE GENERATED FEATURES
# ============================================================

if feature_data.columns.duplicated().any():
    duplicate_features = feature_data.columns[
        feature_data.columns.duplicated()
    ].tolist()

    raise ValueError(
        "Duplicate generated feature names found: "
        f"{duplicate_features}"
    )

# Replace infinite values.
feature_data = feature_data.replace(
    [np.inf, -np.inf],
    np.nan
)

# Check for missing values in generated features.
if feature_data.isnull().sum().sum() != 0:

    missing_feature_columns = feature_data.columns[
        feature_data.isnull().any()
    ].tolist()

    raise ValueError(
        "Generated signal features contain missing values in: "
        f"{missing_feature_columns}"
    )


# ============================================================
# 10. COMBINE ORIGINAL AND GENERATED FEATURES
# ============================================================

signal_features_df = pd.concat(
    [
        df,
        feature_data
    ],
    axis=1
)

# Check for duplicate columns after merging.
if signal_features_df.columns.duplicated().any():

    duplicate_columns = signal_features_df.columns[
        signal_features_df.columns.duplicated()
    ].tolist()

    raise ValueError(
        "Duplicate columns found after combining datasets: "
        f"{duplicate_columns}"
    )


# ============================================================
# 11. FINAL OUTPUT VALIDATION
# ============================================================

if signal_features_df.isnull().sum().sum() != 0:
    missing_columns = signal_features_df.columns[
        signal_features_df.isnull().any()
    ].tolist()

    raise ValueError(
        "Final signal-processing output contains missing values "
        f"in: {missing_columns}"
    )

if TARGET_COLUMN not in signal_features_df.columns:
    raise ValueError(
        f"Target column '{TARGET_COLUMN}' is missing "
        "from the output."
    )

if "UDI" not in signal_features_df.columns:
    raise ValueError(
        "UDI is missing from the output."
    )

if len(signal_features_df) != len(df):
    raise ValueError(
        "The number of rows changed during signal processing."
    )


# ============================================================
# 12. SAVE SIGNAL FEATURES
# ============================================================

signal_features_df.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\nSignal processing completed successfully.")
print("Output shape:", signal_features_df.shape)
print(
    "Number of generated features:",
    len(feature_data.columns)
)
print("Saved file:", OUTPUT_FILE)

print("\nGenerated signal features:")
for feature in feature_data.columns:
    print(f"- {feature}")


# ============================================================
# 13. FINAL SUMMARY
# ============================================================

print("\n" + "=" * 60)
print("STEP 2 COMPLETED SUCCESSFULLY")
print("=" * 60)

print(f"Total rows: {len(signal_features_df)}")
print(f"Total columns: {len(signal_features_df.columns)}")
print(f"Rolling-window size: {WINDOW_SIZE}")
print(f"Target column retained: {TARGET_COLUMN}")
print("UDI retained: YES")
print("Missing values: 0")
print("=" * 60)