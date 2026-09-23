from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_FILE = PROJECT_ROOT / "data" / "raw" / "ai4i2020.csv"
OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "cleaned_dataset.csv"
)

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)


# ============================================================
# CONFIGURATION
# ============================================================

TARGET_COLUMN = "Machine_failure"

# Product_ID is an identifier and is not useful for modeling.
# UDI is intentionally retained because it is required later
# for external-context data merging.
IDENTIFIER_COLUMNS = [
    "Product_ID"
]


# ============================================================
# 1. LOAD DATASET
# ============================================================

print("\nLoading dataset...")

if not RAW_FILE.exists():
    raise FileNotFoundError(
        f"Raw dataset was not found at:\n{RAW_FILE}"
    )

df = pd.read_csv(RAW_FILE)

print("Original shape:", df.shape)

print("\nOriginal columns:")
print(df.columns.tolist())


# ============================================================
# 2. STANDARDIZE COLUMN NAMES
# ============================================================

df.columns = (
    df.columns
    .str.strip()
    .str.replace(" ", "_", regex=False)
)

print("\nStandardized columns:")
print(df.columns.tolist())


# ============================================================
# 3. REMOVE DUPLICATE RECORDS
# ============================================================

duplicate_count = int(df.duplicated().sum())

df = (
    df
    .drop_duplicates()
    .reset_index(drop=True)
)

print("\nDuplicates removed:", duplicate_count)


# ============================================================
# 4. HANDLE MISSING VALUES
# ============================================================

missing_before = int(
    df.isnull().sum().sum()
)

print("Missing values before:", missing_before)

# Numeric columns
numeric_columns = df.select_dtypes(
    include=[np.number]
).columns

for column in numeric_columns:
    if df[column].isnull().any():
        df[column] = df[column].fillna(
            df[column].median()
        )

# Categorical columns
categorical_columns = df.select_dtypes(
    exclude=[np.number]
).columns

for column in categorical_columns:
    if df[column].isnull().any():
        mode_values = df[column].mode()

        if not mode_values.empty:
            df[column] = df[column].fillna(
                mode_values.iloc[0]
            )

missing_after = int(
    df.isnull().sum().sum()
)

print("Missing values after:", missing_after)


# ============================================================
# 5. VALIDATE AND REMOVE IDENTIFIER COLUMNS
# ============================================================

removed_identifiers = [
    column
    for column in IDENTIFIER_COLUMNS
    if column in df.columns
]

df = df.drop(
    columns=removed_identifiers,
    errors="ignore"
)

print(
    "\nIdentifier columns removed:",
    removed_identifiers
)


# ============================================================
# 6. VALIDATE UDI COLUMN
# ============================================================

# UDI is retained for external-context fusion in a later step.

if "UDI" not in df.columns:
    raise ValueError(
        "UDI is missing. It is required for context fusion."
    )

if df["UDI"].isnull().any():
    raise ValueError(
        "UDI contains missing values."
    )

if df["UDI"].duplicated().any():
    raise ValueError(
        "Duplicate UDI values were found."
    )


# ============================================================
# 7. VALIDATE DATA TYPES
# ============================================================

# Type and the target column are handled separately.
# All other columns are converted to numeric when possible.

for column in df.columns:

    if column not in ["Type", TARGET_COLUMN]:

        converted_values = pd.to_numeric(
            df[column],
            errors="coerce"
        )

        # Convert only when conversion does not introduce
        # additional missing values.
        if not converted_values.isnull().any():
            df[column] = converted_values


# ============================================================
# 8. VALIDATE TARGET COLUMN
# ============================================================

if TARGET_COLUMN not in df.columns:
    raise ValueError(
        f"Required target column '{TARGET_COLUMN}' "
        "was not found."
    )

# Ensure that the target is numeric.
df[TARGET_COLUMN] = pd.to_numeric(
    df[TARGET_COLUMN],
    errors="coerce"
)

if df[TARGET_COLUMN].isnull().any():
    raise ValueError(
        f"Target column '{TARGET_COLUMN}' contains "
        "invalid or missing values."
    )

print("\nTarget distribution:")
print(
    df[TARGET_COLUMN].value_counts(
        dropna=False
    )
)


# ============================================================
# 9. FINAL DATA QUALITY CHECKS
# ============================================================

if df.isnull().sum().sum() != 0:
    missing_columns = df.columns[
        df.isnull().any()
    ].tolist()

    raise ValueError(
        "Dataset still contains missing values in: "
        f"{missing_columns}"
    )

if df.duplicated().sum() != 0:
    raise ValueError(
        "Dataset still contains duplicate rows."
    )

# The AI4I dataset uses binary machine-failure labels.
unique_target_values = set(
    df[TARGET_COLUMN].unique()
)

if not unique_target_values.issubset({0, 1}):
    raise ValueError(
        f"The target column '{TARGET_COLUMN}' must contain "
        f"only 0 and 1. Found: {unique_target_values}"
    )


# ============================================================
# 10. FINAL COLUMN VALIDATION
# ============================================================

# The target must remain in the cleaned dataset.
# It will be separated into X and y during a later step.

if TARGET_COLUMN not in df.columns:
    raise ValueError(
        f"Target column '{TARGET_COLUMN}' is missing "
        "from the final dataset."
    )

print("\nTarget column retained:", TARGET_COLUMN)


# ============================================================
# 11. SAVE CLEANED DATASET
# ============================================================

df.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\nPreprocessing completed successfully.")
print("Final shape:", df.shape)
print("Saved file:", OUTPUT_FILE)

print("\nFinal columns:")
print(df.columns.tolist())


# ============================================================
# 12. FINAL SUMMARY
# ============================================================

print("\n" + "=" * 60)
print("STEP 1 COMPLETED SUCCESSFULLY")
print("=" * 60)

print(f"Total rows: {len(df)}")
print(f"Total columns: {len(df.columns)}")
print(f"Target column: {TARGET_COLUMN}")
print(
    "Target values:",
    sorted(df[TARGET_COLUMN].unique().tolist())
)
print(
    "Target column retained in cleaned dataset: YES"
)
print("=" * 60)