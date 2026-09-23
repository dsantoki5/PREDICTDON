from pathlib import Path
import pandas as pd


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SIGNAL_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "signal_features.csv"
)

EXTERNAL_FILE = (
    PROJECT_ROOT
    / "data"
    / "external"
    / "external_context.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "context_fused_dataset.csv"
)

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)


# ============================================================
# CONFIGURATION
# ============================================================

MERGE_KEY = "UDI"

PROTECTED_COLUMNS = {
    "Machine_failure",
    "TWF",
    "HDF",
    "PWF",
    "OSF",
    "RNF"
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def standardize_columns(dataframe):
    """Standardize column names consistently across datasets."""

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


def validate_columns(dataframe, dataset_name):
    """Check for duplicate and empty column names."""

    if dataframe.columns.duplicated().any():
        duplicate_columns = (
            dataframe.columns[
                dataframe.columns.duplicated()
            ].tolist()
        )

        raise ValueError(
            f"{dataset_name} contains duplicate columns: "
            f"{duplicate_columns}"
        )

    empty_columns = [
        column
        for column in dataframe.columns
        if not str(column).strip()
    ]

    if empty_columns:
        raise ValueError(
            f"{dataset_name} contains empty column names."
        )


def validate_udi(dataframe, dataset_name):
    """Validate the merge key."""

    if MERGE_KEY not in dataframe.columns:
        raise ValueError(
            f"{MERGE_KEY} is missing from {dataset_name}."
        )

    if dataframe[MERGE_KEY].isnull().any():
        raise ValueError(
            f"{dataset_name} contains missing {MERGE_KEY} values."
        )

    if dataframe[MERGE_KEY].duplicated().any():
        raise ValueError(
            f"{dataset_name} contains duplicate {MERGE_KEY} values."
        )


# ============================================================
# 1. CHECK INPUT FILES
# ============================================================

print("\nLoading signal and external-context datasets...")

if not SIGNAL_FILE.exists():
    raise FileNotFoundError(
        f"Signal file not found: {SIGNAL_FILE}"
    )

if not EXTERNAL_FILE.exists():
    raise FileNotFoundError(
        f"External context file not found: {EXTERNAL_FILE}"
    )


# ============================================================
# 2. LOAD DATASETS
# ============================================================

signal_df = pd.read_csv(SIGNAL_FILE)
context_df = pd.read_csv(EXTERNAL_FILE)

if signal_df.empty:
    raise ValueError("The signal dataset is empty.")

if context_df.empty:
    raise ValueError("The external-context dataset is empty.")

print("Signal dataset shape:", signal_df.shape)
print("External context shape:", context_df.shape)


# ============================================================
# 3. STANDARDIZE COLUMN NAMES
# ============================================================

signal_df = standardize_columns(signal_df)
context_df = standardize_columns(context_df)

validate_columns(signal_df, "Signal dataset")
validate_columns(context_df, "External-context dataset")


# ============================================================
# 4. VALIDATE MERGE KEY
# ============================================================

validate_udi(signal_df, "Signal dataset")
validate_udi(context_df, "External-context dataset")


# ============================================================
# 5. CHECK EXTERNAL-CONTEXT MISSING VALUES
# ============================================================

context_missing = context_df.isnull().sum()

if context_missing.sum() > 0:
    context_missing = context_missing[
        context_missing > 0
    ]

    raise ValueError(
        "Missing values found in external-context dataset:\n"
        f"{context_missing}"
    )


# ============================================================
# 6. CHECK UDI COVERAGE
# ============================================================

signal_ids = set(signal_df[MERGE_KEY])
context_ids = set(context_df[MERGE_KEY])

missing_context_ids = signal_ids - context_ids
unused_context_ids = context_ids - signal_ids

if missing_context_ids:
    raise ValueError(
        "Some signal records have no matching external context. "
        f"Missing records: {len(missing_context_ids)}"
    )

if unused_context_ids:
    raise ValueError(
        "Some external-context records have no matching signal "
        f"record. Unused records: {len(unused_context_ids)}"
    )


# ============================================================
# 7. PROTECT AGAINST TARGET LEAKAGE
# ============================================================

leakage_columns = (
    PROTECTED_COLUMNS.intersection(
        set(context_df.columns)
    )
)

if leakage_columns:
    raise ValueError(
        "Potential target-leakage columns found in external "
        f"context: {sorted(leakage_columns)}. "
        "Remove them before context fusion."
    )


# ============================================================
# 8. PREVENT COLUMN COLLISIONS
# ============================================================

overlapping_columns = (
    set(signal_df.columns)
    .intersection(set(context_df.columns))
    - {MERGE_KEY}
)

if overlapping_columns:
    print("\nOverlapping columns detected:")
    print(sorted(overlapping_columns))

    print(
        "The signal dataset's versions will be retained."
    )

    context_df = context_df.drop(
        columns=list(overlapping_columns)
    )


# ============================================================
# 9. MERGE DATASETS
# ============================================================

print("\nMerging datasets using UDI...")

original_signal_shape = signal_df.shape
original_signal_columns = set(signal_df.columns)

fused_df = signal_df.merge(
    context_df,
    on=MERGE_KEY,
    how="left",
    validate="one_to_one",
    sort=False
)


# ============================================================
# 10. VALIDATE MERGED DATASET
# ============================================================

if len(fused_df) != len(signal_df):
    raise ValueError(
        "Row count changed unexpectedly during context fusion."
    )

if fused_df[MERGE_KEY].duplicated().any():
    raise ValueError(
        "Duplicate UDI values found after context fusion."
    )

if fused_df.isnull().sum().sum() != 0:
    missing_values = fused_df.isnull().sum()
    missing_values = missing_values[
        missing_values > 0
    ]

    raise ValueError(
        "Missing values found after context fusion:\n"
        f"{missing_values}"
    )

missing_original_columns = (
    original_signal_columns - set(fused_df.columns)
)

if missing_original_columns:
    raise ValueError(
        "Original signal columns were lost during fusion: "
        f"{sorted(missing_original_columns)}"
    )


# ============================================================
# 11. SAVE OUTPUT
# ============================================================

fused_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# 12. DISPLAY SUMMARY
# ============================================================

added_columns = [
    column
    for column in fused_df.columns
    if column not in signal_df.columns
]

print("\nContext fusion completed successfully.")
print("=" * 60)
print("Original signal shape:", original_signal_shape)
print("Final fused shape:", fused_df.shape)
print("Final column count:", len(fused_df.columns))
print("Number of context columns added:", len(added_columns))
print("Saved file:", OUTPUT_FILE)

print("\nContext columns added:")
for column in added_columns:
    print(f"- {column}")

print("=" * 60)
print("STEP 3 COMPLETED SUCCESSFULLY")
print("=" * 60)