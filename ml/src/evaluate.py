"""
Evaluation pipeline for PredictCNC LightGBM model.
Authoritative Model: LightGBM_No_SMOTE_Final.joblib
Dataset: ai4i2020.csv (10,000 samples)
"""
import os
import joblib
import pandas as pd
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)
from ml.src.feature_engineering import engineer_features_44, MODEL_FEATURES_44

def evaluate_model(dataset_filename="ai4i2020.csv"):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, "data", "raw", dataset_filename)
    model_path = os.path.join(base_dir, "models", "LightGBM_No_SMOTE_Final.joblib")

    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Dataset not found at {data_path}")

    print(f"Loading authoritative dataset: {data_path}")
    df = pd.read_csv(data_path)

    print(f"Loading authoritative model: {model_path}")
    model = joblib.load(model_path)

    print(f"Generating 44 engineered features on {len(df)} samples...")
    features_list = []
    for i in range(len(df)):
        feats = engineer_features_44(
            air_temp=df.loc[i, "Air temperature [K]"],
            process_temp=df.loc[i, "Process temperature [K]"],
            rotational_speed=df.loc[i, "Rotational speed [rpm]"],
            torque=df.loc[i, "Torque [Nm]"],
            tool_wear=df.loc[i, "Tool wear [min]"],
            machine_type=df.loc[i, "Type"],
            shift="Morning",
            humidity=60.0
        )
        features_list.append(feats)

    X = pd.DataFrame(features_list)[MODEL_FEATURES_44]
    y_preds = model.predict(X)
    y_probs = model.predict_proba(X)

    unique, counts = np.unique(y_preds, return_counts=True)
    dist = {int(u): int(c) for u, c in zip(unique, counts)}

    print("\n" + "="*60)
    print("LIGHTGBM MULTI-CLASS EVALUATION SUMMARY (10,000 SAMPLES)")
    print("="*60)
    print("Predicted Class Breakdown:")
    print(f"  Class 0 (Normal Operation):                 {dist.get(0, 0)} ({dist.get(0, 0)/len(df)*100:.2f}%)")
    print(f"  Class 1 (Degraded / Early Anomaly Warning): {dist.get(1, 0)} ({dist.get(1, 0)/len(df)*100:.2f}%)")
    print(f"  Class 2 (Critical Failure / Breakdown):     {dist.get(2, 0)} ({dist.get(2, 0)/len(df)*100:.2f}%)")

    # Binary breakdown against actual failure column
    actual_fail = df["Machine failure"].values
    predicted_fail_binary = (y_preds == 2).astype(int)

    precision_crit = precision_score(actual_fail, predicted_fail_binary, zero_division=0)
    cm = confusion_matrix(actual_fail, (y_preds > 0).astype(int))

    print(f"\nCritical Failure Precision (Class 2 vs Actual Failure): {precision_crit*100:.2f}%")
    print("\nConfusion Matrix (Normal vs Any Anomaly/Failure Flag):")
    print(cm)

    return {
        "model_name": "LightGBM_No_SMOTE_Final.joblib (v4.2)",
        "dataset": "ai4i2020.csv (10,000 samples)",
        "total_samples": len(df),
        "class_distribution": dist,
        "critical_precision": round(precision_crit * 100.0, 2),
        "confusion_matrix": cm.tolist()
    }

if __name__ == "__main__":
    evaluate_model()
