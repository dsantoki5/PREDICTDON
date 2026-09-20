"
Training Pipeline for PredictCNC
Trains a clean LightGBM classifier on the UCI AI4I 2020 dataset.
"
import os
import joblib
import pandas as pd
import numpy as np
from lightgbm import LGBMClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, f1_score
from feature_engineering import engineer_features, MODEL_FEATURES

def train_model(output_filename=final_lightgbm_model.pkl):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, data, raw, ai4i2020.csv)
    model_dir = os.path.join(base_dir, models)
    os.makedirs(model_dir, exist_ok=True)

    print(Loading data...)
    df = pd.read_csv(data_path)

    tool_wear_rolling = df[Tool wear [min]].rolling(window=10, min_periods=1).mean()
    air_temp_rolling = df[Air temperature [K]].rolling(window=10, min_periods=1).mean()

    features_list = []
    for i in range(len(df)):
        feats = engineer_features(
            air_temp=df.loc[i, Air temperature [K]],
            process_temp=df.loc[i, Process temperature [K]],
            rotational_speed=df.loc[i, Rotational speed [rpm]],
            torque=df.loc[i, Torque [Nm]],
            tool_wear=df.loc[i, Tool wear [min]],
            tool_wear_mean_10=tool_wear_rolling.iloc[i],
            air_temp_mean_10=air_temp_rolling.iloc[i]
        )
        features_list.append(feats)

    X = pd.DataFrame(features_list)[MODEL_FEATURES]
    y = df[Machine failure].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(fTraining LightGBM on {len(X_train)} samples...)
    model = LGBMClassifier(
        n_estimators=200,
        learning_rate=0.05,
        num_leaves=50,
        boosting_type=gbdt,
        random_state=42
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print(\nTest Evaluation:)
    print(classification_report(y_test, y_pred))

    model_path = os.path.join(model_dir, output_filename)
    joblib.dump(model, model_path)
    print(fModel saved to {model_path})

if __name__ == __main__:
    train_model()
