from pathlib import Path
import pandas as pd


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

EXTERNAL_FILE = (
    PROJECT_ROOT
    / "data"
    / "external"
    / "external_context.csv"
)


# ============================================================
# 1. CHECK FILE
# ============================================================

if not EXTERNAL_FILE.exists():
    raise FileNotFoundError(
        f"External context file not found: {EXTERNAL_FILE}"
    )


# ============================================================
# 2. LOAD DATA
# ============================================================

print("\nLoading external-context dataset...")

context_df = pd.read_csv(EXTERNAL_FILE)

if context_df.empty:
    raise ValueError("The external-context dataset is empty.")


# ============================================================
# 3. STANDARDIZE COLUMN NAMES
# ============================================================

def standardize_columns(dataframe):
    dataframe = dataframe.copy()

    dataframe.columns = (
        dataframe.columns
        .astype(str)
        .str.strip()
        .str.replace("[", "", regex=False)
        .str.replace("]", "", regex=False)
        .str.replace("(", "", regex=False)
        .str.replace(")", "", regex=False)
        .str.replace(" ", "_", regex=False)
        .str.replace("/", "_", regex=False)
    )

    return dataframe


context_df = standardize_columns(context_df)


# ============================================================
# 4. DISPLAY BASIC INFORMATION
# ============================================================

print("\nExternal context dataset loaded successfully.")
print("File:", EXTERNAL_FILE)
print("Shape:", context_df.shape)

print("\nColumns:")
print(context_df.columns.tolist())

print("\nData types:")
print(context_df.dtypes)

print("\nMissing values:")
print(context_df.isnull().sum())

print("\nDuplicate rows:", context_df.duplicated().sum())


# ============================================================
# 5. VALIDATE COLUMN NAMES
# ============================================================

if context_df.columns.duplicated().any():
    duplicate_columns = (
        context_df.columns[
            context_df.columns.duplicated()
        ].tolist()
    )

    raise ValueError(
        f"Duplicate column names found: {duplicate_columns}"
    )


# ============================================================
# 6. VALIDATE UDI
# ============================================================

if "UDI" not in context_df.columns:
    raise ValueError(
        "The external-context dataset must contain a 'UDI' column."
    )

if context_df["UDI"].isnull().any():
    raise ValueError(
        "The external-context dataset contains missing UDI values."
    )

if context_df["UDI"].duplicated().any():
    duplicate_udis = context_df.loc[
        context_df["UDI"].duplicated(),
        "UDI"
    ].tolist()

    raise ValueError(
        "Duplicate UDI values found in external context. "
        f"Example IDs: {duplicate_udis[:10]}"
    )


# ============================================================
# 7. CHECK POTENTIAL LEAKAGE COLUMNS
# ============================================================

restricted_columns = {
    "Machine_failure",
    "TWF",
    "HDF",
    "PWF",
    "OSF",
    "RNF"
}

detected_restricted_columns = (
    restricted_columns.intersection(context_df.columns)
)

if detected_restricted_columns:
    print(
        "\nWARNING: Potential target-leakage columns detected:"
    )
    print(sorted(detected_restricted_columns))
    print(
        "These columns must not be used as external model features."
    )


# ============================================================
# 8. PREVIEW DATA
# ============================================================

print("\nFirst five rows:")
print(context_df.head())

print("\nExternal-context inspection completed.")