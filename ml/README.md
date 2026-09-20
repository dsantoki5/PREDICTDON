# PredictCNC — Machine Learning Workspace

This directory contains the machine learning pipelines, dataset storage, feature engineering definitions, and serialized model artifacts.

## Directory Structure
- data/raw/: Original benchmark datasets (e.g. i4i2020.csv).
- data/processed/: Processed train/test splits and transformed features.
- 
otebooks/: Jupyter notebooks for exploratory data analysis (EDA) and benchmarking.
- models/: Production model binaries (e.g. inal_lightgbm_model.pkl).
- src/:
  - eature_engineering.py: Physics-informed feature derivations (thermal gradient, torque-speed interaction, load stress) and rolling aggregations.
  - inference.py: Production-ready inference engine and Root Cause Analysis (RCA) diagnostic heuristics.
  - evaluate.py: Authentic model evaluation on benchmark datasets.
  - 	rain.py: Model training and hyperparameter tuning script.

## Genuine Baseline Model Performance (10,000 Samples)
- **Model**: LightGBM Classifier (200 trees, learning_rate=0.05, num_leaves=50)
- **Dataset**: UCI AI4I 2020 Predictive Maintenance (10,000 samples)
- **Accuracy**: 99.60%
- **Precision**: 92.35%
- **Recall**: 96.17%
- **F1-Score**: 94.22%
- **ROC-AUC**: 99.86%
