"""
Training Pipeline for PredictCNC
Authoritative model: LightGBM_No_SMOTE_Final.joblib
NOTE: Model training on the updated dataset is currently pending dataset upload.
"""
import os
import sys

def train_model(dataset_filename="CNC_Maintenance_Dataset_Updated.csv"):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, "data", "raw", dataset_filename)
    
    if not os.path.exists(data_path):
        print(f"[STATUS] New updated dataset not found at {data_path}.")
        print("[STATUS] Training is halted as per project policy. Do NOT retrain using the legacy dataset.")
        print(f"Please place the new updated dataset at: {data_path}")
        return False
        
    print(f"Loading updated dataset from {data_path}...")
    # Training pipeline implementation on new dataset
    return True

if __name__ == "__main__":
    train_model()
