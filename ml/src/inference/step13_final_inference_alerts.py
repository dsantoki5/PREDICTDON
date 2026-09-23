from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd


# ============================================================
# STEP 13: FINAL MODEL INFERENCE AND ALERT GENERATION
# ============================================================

print("\n" + "=" * 70)
print("STEP 13: FINAL MODEL INFERENCE AND ALERT GENERATION")
print("=" * 70)


# ------------------------------------------------------------
# 1. PROJECT PATHS
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

TEST_DATA_PATH = (
    PROJECT_ROOT / "data" / "processed" / "test_dataset.csv"
)

MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "final_models"
    / "LightGBM_No_SMOTE_Final.joblib"
)

THRESHOLD_CONFIG_PATH = (
    PROJECT_ROOT
    / "outputs"
    / "step_11_final_model"
    / "final_threshold_configuration.json"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "step_13_inference"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# 2. CONFIGURATION
# ------------------------------------------------------------

TARGET_COLUMN = "Machine_Status_Code"
CRITICAL_CLASS = 2

# Fallback threshold in case the configuration file
# does not contain a selected threshold.
DEFAULT_CRITICAL_THRESHOLD = 0.10


# ------------------------------------------------------------
# 3. LOAD TEST DATA
# ------------------------------------------------------------

if not TEST_DATA_PATH.exists():
    raise FileNotFoundError(
        f"Test dataset not found:\n{TEST_DATA_PATH}"
    )

test_df = pd.read_csv(TEST_DATA_PATH)

print(f"Test dataset loaded: {test_df.shape}")


if TARGET_COLUMN not in test_df.columns:
    raise ValueError(
        f"Target column '{TARGET_COLUMN}' was not found "
        "in the test dataset."
    )


# Preserve original row information for traceability.
original_test_df = test_df.copy()

X_test = test_df.drop(columns=[TARGET_COLUMN])
y_test = test_df[TARGET_COLUMN].astype(int)


# ------------------------------------------------------------
# 4. LOAD FINAL MODEL
# ------------------------------------------------------------

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"Final model not found:\n{MODEL_PATH}"
    )

model = joblib.load(MODEL_PATH)

print(f"Final model loaded from:\n{MODEL_PATH}")
print(f"Model type: {type(model).__name__}")


# ------------------------------------------------------------
# 5. LOAD CRITICAL THRESHOLD
# ------------------------------------------------------------

selected_threshold = DEFAULT_CRITICAL_THRESHOLD
selected_model_name = "LightGBM"
selected_strategy = "No_SMOTE"

if THRESHOLD_CONFIG_PATH.exists():

    with open(THRESHOLD_CONFIG_PATH, "r", encoding="utf-8") as file:
        threshold_config = json.load(file)

    selected_threshold = threshold_config.get(
        "selected_threshold",
        threshold_config.get(
            "threshold",
            DEFAULT_CRITICAL_THRESHOLD
        )
    )

    selected_model_name = threshold_config.get(
        "selected_model",
        threshold_config.get(
            "model_name",
            selected_model_name
        )
    )

    selected_strategy = threshold_config.get(
        "selected_strategy",
        threshold_config.get(
            "sampling_strategy",
            selected_strategy
        )
    )

else:
    print(
        "Warning: Threshold configuration file not found. "
        f"Using default threshold: {DEFAULT_CRITICAL_THRESHOLD}"
    )

selected_threshold = float(selected_threshold)

print(f"Selected model: {selected_model_name}")
print(f"Selected strategy: {selected_strategy}")
print(f"Critical class: {CRITICAL_CLASS}")
print(f"Critical-class threshold: {selected_threshold}")


# ------------------------------------------------------------
# 6. GENERATE PROBABILITY PREDICTIONS
# ------------------------------------------------------------

if not hasattr(model, "predict_proba"):
    raise AttributeError(
        "The loaded model does not support predict_proba()."
    )

probabilities = model.predict_proba(X_test)

print(f"Probability matrix shape: {probabilities.shape}")


# Determine the class index for the critical class.
if hasattr(model, "classes_"):
    model_classes = list(model.classes_)
else:
    model_classes = [0, 1, 2]

if CRITICAL_CLASS not in model_classes:
    raise ValueError(
        f"Critical class {CRITICAL_CLASS} was not found in "
        f"model classes: {model_classes}"
    )

critical_class_index = model_classes.index(CRITICAL_CLASS)

critical_probabilities = probabilities[:, critical_class_index]


# Initial prediction using the class with the highest probability.
argmax_indices = np.argmax(probabilities, axis=1)
predicted_classes = np.array(
    [model_classes[index] for index in argmax_indices],
    dtype=int
)


# ------------------------------------------------------------
# 7. APPLY CRITICAL-CLASS THRESHOLD
# ------------------------------------------------------------

# If the probability of the critical class reaches the
# configured threshold, classify the machine as critical.
critical_alert_mask = (
    critical_probabilities >= selected_threshold
)

threshold_predictions = predicted_classes.copy()
threshold_predictions[critical_alert_mask] = CRITICAL_CLASS


print(
    "Critical-class threshold applied successfully."
)

print(
    f"Predicted critical machines: "
    f"{int(np.sum(threshold_predictions == CRITICAL_CLASS))}"
)

print(
    f"Critical alerts generated: "
    f"{int(np.sum(critical_alert_mask))}"
)


# ------------------------------------------------------------
# 8. CREATE PREDICTION REPORT
# ------------------------------------------------------------

prediction_report = original_test_df.copy()

prediction_report["Predicted_Status_Code"] = threshold_predictions
prediction_report["Critical_Class_Probability"] = critical_probabilities
prediction_report["Critical_Alert"] = critical_alert_mask

prediction_report["Prediction_Status"] = np.where(
    threshold_predictions == CRITICAL_CLASS,
    "CRITICAL",
    np.where(
        threshold_predictions == 1,
        "WARNING",
        "NORMAL"
    )
)


# Add individual class probabilities when available.
for index, class_label in enumerate(model_classes):
    prediction_report[
        f"Probability_Class_{class_label}"
    ] = probabilities[:, index]


# Add row-level identifier if no machine identifier exists.
if "Machine_ID" not in prediction_report.columns:
    prediction_report.insert(
        0,
        "Inference_Row_ID",
        range(1, len(prediction_report) + 1)
    )


# ------------------------------------------------------------
# 9. CREATE ALERT REPORT
# ------------------------------------------------------------

alert_report = prediction_report[
    prediction_report["Critical_Alert"] == True
].copy()

alert_report = alert_report.sort_values(
    by="Critical_Class_Probability",
    ascending=False
)

alert_report.insert(
    0,
    "Alert_ID",
    range(1, len(alert_report) + 1)
)

alert_report["Alert_Level"] = "CRITICAL"

alert_report["Recommended_Action"] = (
    "Schedule immediate inspection and preventive maintenance"
)


# ------------------------------------------------------------
# 10. SAVE OUTPUT FILES
# ------------------------------------------------------------

predictions_path = OUTPUT_DIR / "final_predictions.csv"
alerts_path = OUTPUT_DIR / "critical_machine_alerts.csv"
summary_path = OUTPUT_DIR / "inference_summary.json"

prediction_report.to_csv(
    predictions_path,
    index=False
)

alert_report.to_csv(
    alerts_path,
    index=False
)


# ------------------------------------------------------------
# 11. CREATE SUMMARY
# ------------------------------------------------------------

prediction_counts = {
    str(int(label)): int(
        np.sum(threshold_predictions == label)
    )
    for label in model_classes
}

summary = {
    "step": 13,
    "step_name": "Final Model Inference and Alert Generation",
    "model_name": selected_model_name,
    "sampling_strategy": selected_strategy,
    "model_file": str(MODEL_PATH),
    "test_dataset": str(TEST_DATA_PATH),
    "target_column": TARGET_COLUMN,
    "critical_class": CRITICAL_CLASS,
    "critical_threshold": selected_threshold,
    "total_records": int(len(prediction_report)),
    "total_critical_alerts": int(len(alert_report)),
    "prediction_counts": prediction_counts,
    "critical_alert_percentage": round(
        (len(alert_report) / len(prediction_report)) * 100,
        2
    ),
    "output_files": {
        "predictions": str(predictions_path),
        "critical_alerts": str(alerts_path),
        "summary": str(summary_path)
    }
}

with open(summary_path, "w", encoding="utf-8") as file:
    json.dump(summary, file, indent=4)


# ------------------------------------------------------------
# 12. DISPLAY SUMMARY
# ------------------------------------------------------------

print("\n" + "-" * 70)
print("INFERENCE SUMMARY")
print("-" * 70)

print(f"Total machines evaluated: {len(prediction_report)}")
print(f"Total critical alerts: {len(alert_report)}")
print(
    f"Critical alert percentage: "
    f"{summary['critical_alert_percentage']}%"
)

print("\nPrediction distribution:")

for label, count in prediction_counts.items():
    print(f"  Class {label}: {count}")


print("\nGenerated files:")

print(f"1. Final predictions:")
print(f"   {predictions_path}")

print(f"2. Critical machine alerts:")
print(f"   {alerts_path}")

print(f"3. Inference summary:")
print(f"   {summary_path}")


print("\n" + "=" * 70)
print("STEP 13 COMPLETED SUCCESSFULLY")
print("=" * 70)