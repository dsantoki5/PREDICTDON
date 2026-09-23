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
    / "context_fused_dataset.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "engineered_dataset.csv"
)

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)


# ============================================================
# CONFIGURATION
# ============================================================

ID_COLUMN = "UDI"
BINARY_FAILURE_COLUMN = "Machine_failure"
WINDOW_SIZE = 10

REQUIRED_COLUMNS = [
    "Air_temperature_K",
    "Process_temperature_K",
    "Rotational_speed_rpm",
    "Torque_Nm",
    "Tool_wear_min",
    "ambient_temperature",
    "load_density",
    "humidity",
    "vibration_level",
    "maintenance_due"
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def validate_required_columns(dataframe, columns):
    """Validate that all required columns exist."""

    missing_columns = [
        column
        for column in columns
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )


def convert_columns_to_numeric(dataframe, columns):
    """Convert selected columns to numeric safely."""

    for column in columns:
        converted = pd.to_numeric(
            dataframe[column],
            errors="coerce"
        )

        if converted.isnull().any():
            raise ValueError(
                f"Column '{column}' contains missing or "
                "non-numeric values."
            )

        dataframe[column] = converted

    return dataframe


# ============================================================
# 1. LOAD DATA
# ============================================================

print("\nLoading context-fused dataset...")

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Input file not found: {INPUT_FILE}"
    )

df = pd.read_csv(INPUT_FILE)

if df.empty:
    raise ValueError("Input dataset is empty.")

original_shape = df.shape

print("Input shape:", original_shape)


# ============================================================
# 2. VALIDATE COLUMNS
# ============================================================

validate_required_columns(
    df,
    [
        ID_COLUMN,
        BINARY_FAILURE_COLUMN,
        *REQUIRED_COLUMNS
    ]
)


# ============================================================
# 3. VALIDATE IDENTIFIER AND BINARY FAILURE COLUMN
# ============================================================

if df[ID_COLUMN].isnull().any():
    raise ValueError("Missing UDI values detected.")

if df[ID_COLUMN].duplicated().any():
    raise ValueError("Duplicate UDI values detected.")

failure_values = set(
    df[BINARY_FAILURE_COLUMN].dropna().unique()
)

if not failure_values.issubset({0, 1}):
    raise ValueError(
        "Machine_failure must contain only 0 and 1."
    )


# ============================================================
# 4. CONVERT REQUIRED COLUMNS TO NUMERIC
# ============================================================

print("\nValidating numeric columns...")

df = convert_columns_to_numeric(
    df,
    REQUIRED_COLUMNS
)


# ============================================================
# 5. CREATE ENGINEERED FEATURES
# ============================================================

print("\nCreating engineered features...")

ENGINEERED_FEATURES = []


# ------------------------------------------------------------
# 5.1 Ambient-temperature difference
# ------------------------------------------------------------

df["ambient_difference"] = (
    df["Air_temperature_K"]
    - df["ambient_temperature"]
)

ENGINEERED_FEATURES.append("ambient_difference")


# ------------------------------------------------------------
# 5.2 Mechanical load
# ------------------------------------------------------------

df["load_stress"] = (
    df["Torque_Nm"]
    * df["Rotational_speed_rpm"]
)

ENGINEERED_FEATURES.append("load_stress")


# ------------------------------------------------------------
# 5.3 Load-density interaction
# ------------------------------------------------------------

df["load_density_interaction"] = (
    df["load_density"]
    * df["Torque_Nm"]
)

ENGINEERED_FEATURES.append("load_density_interaction")


# ------------------------------------------------------------
# 5.4 Temperature-humidity interaction
# ------------------------------------------------------------

df["temperature_humidity_interaction"] = (
    df["Process_temperature_K"]
    * df["humidity"]
)

ENGINEERED_FEATURES.append(
    "temperature_humidity_interaction"
)


# ------------------------------------------------------------
# 5.5 Vibration-load interaction
# ------------------------------------------------------------

df["vibration_stress"] = (
    df["vibration_level"]
    * df["load_density"]
)

ENGINEERED_FEATURES.append("vibration_stress")


# ------------------------------------------------------------
# 5.6 Torque-to-speed ratio
# ------------------------------------------------------------

df["torque_speed_ratio"] = (
    df["Torque_Nm"]
    / (df["Rotational_speed_rpm"] + 1e-9)
)

ENGINEERED_FEATURES.append("torque_speed_ratio")


# ------------------------------------------------------------
# 5.7 Maintenance-load interaction
# ------------------------------------------------------------

df["maintenance_load_interaction"] = (
    df["maintenance_due"]
    * df["load_density"]
)

ENGINEERED_FEATURES.append(
    "maintenance_load_interaction"
)


# ============================================================
# 6. CREATE ROLLING ENGINEERED FEATURES
# ============================================================

print("\nCreating rolling engineered features...")

# IMPORTANT:
# These calculations use the dataset's row order.
# They do not represent verified chronological machine history.

df["tool_wear_mean_10"] = (
    df["Tool_wear_min"]
    .rolling(
        window=WINDOW_SIZE,
        min_periods=1
    )
    .mean()
)

ENGINEERED_FEATURES.append("tool_wear_mean_10")


df["rpm_std_10"] = (
    df["Rotational_speed_rpm"]
    .rolling(
        window=WINDOW_SIZE,
        min_periods=1
    )
    .std()
    .fillna(0)
)

ENGINEERED_FEATURES.append("rpm_std_10")


df["torque_std_10"] = (
    df["Torque_Nm"]
    .rolling(
        window=WINDOW_SIZE,
        min_periods=1
    )
    .std()
    .fillna(0)
)

ENGINEERED_FEATURES.append("torque_std_10")


df["load_density_mean_10"] = (
    df["load_density"]
    .rolling(
        window=WINDOW_SIZE,
        min_periods=1
    )
    .mean()
)

ENGINEERED_FEATURES.append("load_density_mean_10")


# ============================================================
# 7. HANDLE INVALID VALUES
# ============================================================

print("\nChecking engineered features...")

df = df.replace(
    [np.inf, -np.inf],
    np.nan
)

engineered_missing = df[
    ENGINEERED_FEATURES
].isnull().sum()

if engineered_missing.sum() > 0:
    print("Missing values in engineered features:")
    print(
        engineered_missing[
            engineered_missing > 0
        ]
    )

    raise ValueError(
        "Invalid values detected in engineered features."
    )


# ============================================================
# 8. FINAL VALIDATION
# ============================================================

if df.isnull().sum().sum() != 0:
    missing_values = df.isnull().sum()
    missing_values = missing_values[
        missing_values > 0
    ]

    raise ValueError(
        "Missing values remain in the dataset:\n"
        f"{missing_values}"
    )

if df[ID_COLUMN].duplicated().any():
    raise ValueError("Duplicate UDI values found.")

if len(df) != original_shape[0]:
    raise ValueError(
        "Row count changed unexpectedly."
    )

if BINARY_FAILURE_COLUMN not in df.columns:
    raise ValueError(
        "Machine_failure column was lost."
    )


# ============================================================
# 9. SAVE DATASET
# ============================================================

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# 10. DISPLAY SUMMARY
# ============================================================

print("\nFeature engineering completed successfully.")
print("=" * 60)
print("Original shape:", original_shape)
print("Output shape:", df.shape)
print("New features created:", len(ENGINEERED_FEATURES))
print("UDI retained:", ID_COLUMN)
print("Machine_failure retained:", BINARY_FAILURE_COLUMN)
print("Missing values:", int(df.isnull().sum().sum()))
print("Saved file:", OUTPUT_FILE)

print("\nNew feature names:")
for feature in ENGINEERED_FEATURES:
    print(f"- {feature}")

print("=" * 60)
print("STEP 4 COMPLETED SUCCESSFULLY")
print("=" * 60)