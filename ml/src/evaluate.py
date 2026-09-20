"""
Evaluation pipeline for PredictCNC LightGBM model.
Computes genuine metrics against the UCI AI4I 2020 Predictive Maintenance Dataset.
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
    roc_auc_score,
    confusion_matrix,
    classification_report
)
from feature_engineering import engineer_features, create_feature_dataframe, MODEL_FEATURES

def evaluate_model():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, "data", "raw", "ai4i2020.csv")
    model_path = os.path.join(base_dir, "models", "final_lightgbm_model.pkl")

    print(f"Loading dataset: {data_path}")
    df = pd.read_csv(data_path)

    tool_wear_rolling = df["Tool wear [min]"].rolling(window=10, min_periods=1).mean()
    air_temp_rolling = df["Air temperature [K]"].rolling(window=10, min_periods=1).mean()

    features_list = []
    for i in range(len(df)):
        feats = engineer_features(
            air_temp=df.loc[i, "Air temperature [K]"],
            process_temp=df.loc[i, "Process temperature [K]"],
            rotational_speed=df.loc[i, "Rotational speed [rpm]"],
            torque=df.loc[i, "Torque [Nm]"],
            tool_wear=df.loc[i, "Tool wear [min]"],
            tool_wear_mean_10=tool_wear_rolling.iloc[i],
            air_temp_mean_10=air_temp_rolling.iloc[i]
        )
        features_list.append(feats)

    X = pd.DataFrame(features_list)[MODEL_FEATURES]
    y_true = df["Machine failure"].values

    print(f"Loading model: {model_path}")
    model = joblib.load(model_path)

    y_pred = model.predict(X)
    y_prob = model.predict_proba(X)[:, 1]

    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    roc = roc_auc_score(y_true, y_prob)
    cm = confusion_matrix(y_true, y_pred)

    print("\n" + "="*50)
    print("GENUINE EVALUATION RESULTS (10,000 Samples)")
    print("="*50)
    print(f"Accuracy:  {acc*100:.2f}%")
    print(f"Precision: {prec*100:.2f}%")
    print(f"Recall:    {rec*100:.2f}%")
    print(f"F1-Score:  {f1*100:.2f}%")
    print(f"ROC-AUC:   {roc*100:.2f}%")
    print("\nConfusion Matrix:")
    print(cm)
    print("\nClassification Report:")
    print(classification_report(y_true, y_pred, target_names=["Normal", "Failure"]))

    return {
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1_score": f1,
        "roc_auc": roc,
        "confusion_matrix": cm.tolist()
    }

if __name__ == "__main__":
    evaluate_model()
