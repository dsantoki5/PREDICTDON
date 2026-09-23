# Predictive Maintenance Using Machine Learning

## SEM-7 Project Report

---

## 1. Project Overview

### 1.1 Project Title

**Predictive Maintenance Using Machine Learning**

### 1.2 Project Objective

The objective of this project is to develop a machine-learning-based predictive maintenance system that classifies machine operating conditions into three health-status categories:

* **Class 0:** Normal
* **Class 1:** Warning
* **Class 2:** Critical

The system uses machine operating parameters, engineered statistical features, contextual information, and machine-type indicators to identify potentially critical operating conditions.

### 1.3 Project Workflow

The project follows this pipeline:

1. Data preprocessing
2. Signal preprocessing
3. Context integration
4. Feature engineering
5. Target creation
6. Feature selection
7. Baseline model training
8. Hyperparameter tuning
9. Model evaluation
10. SMOTE-based class-imbalance experiments
11. Threshold optimization
12. SHAP explainability
13. Final documentation

---

## 2. Dataset Description

The processed dataset contains machine-operating and contextual features.

The final datasets contain:

* Training samples: **8,000**
* Testing samples: **2,000**
* Input features: **24**
* Target column: `Machine_Status_Code`

### 2.1 Target Distribution

| Dataset      | Class 0 | Class 1 | Class 2 |
| ------------ | ------: | ------: | ------: |
| Training set |   4,038 |   3,450 |     512 |
| Test set     |   1,009 |     863 |     128 |

Class 2 represents the critical operating condition and is the minority class.

---

## 3. Data Preprocessing and Leakage Prevention

Data preprocessing included cleaning, transformation, and preparation of the machine-operating variables.

To reduce target leakage, the following target-derived or leakage-prone columns were removed:

* `UDI`
* `Machine_failure`
* `Machine_Status`
* `health_risk_score`
* `TWF`
* `HDF`
* `PWF`
* `OSF`
* `RNF`
* `Tool_wear_min`
* `Tool_wear_min_rolling_mean`
* `Tool_wear_min_rolling_std`
* `Tool_wear_min_rolling_min`
* `Tool_wear_min_rolling_max`
* `tool_wear_change`
* `tool_wear_mean_10`
* `Tool_wear_min_change`
* `vibration_level`
* `vibration_stress`

The final modelling dataset contains 24 predictor variables.

The preprocessing pipeline was fitted on the training data and then applied to the test data.

---

## 4. Feature Engineering

Feature engineering generated additional variables from the machine-operating parameters.

The engineered features included:

* Change in rotational speed
* Change in torque
* Rolling mean of torque
* Rolling maximum of torque
* Rolling standard deviation of torque
* Rolling minimum of rotational speed
* Rolling mean of rotational speed
* Rolling standard deviation of rotational speed
* Temperature difference
* Ambient temperature difference
* Changes in air temperature
* Changes in process temperature
* Rolling temperature variability
* Machine-type indicators
* Shift indicators
* Maintenance-related indicators

These features represent machine operating levels, changes in operating conditions, and short-range variability.

---

## 5. Final Selected Features

The final model used the following 24 features:

1. `Rotational_speed_rpm`
2. `Torque_Nm`
3. `Rotational_speed_rpm_change`
4. `Torque_Nm_change`
5. `Torque_Nm_rolling_max`
6. `Rotational_speed_rpm_rolling_min`
7. `Process_temperature_K_rolling_std`
8. `Air_temperature_K`
9. `temperature_difference`
10. `Rotational_speed_rpm_rolling_std`
11. `Torque_Nm_rolling_mean`
12. `ambient_difference`
13. `Air_temperature_K_change`
14. `Torque_Nm_rolling_std`
15. `Rotational_speed_rpm_rolling_mean`
16. `humidity`
17. `Air_temperature_K_rolling_std`
18. `Process_temperature_K_change`
19. `Type_L`
20. `Type_M`
21. `Process_temperature_K`
22. `shift_Night_True`
23. `shift_Morning_True`
24. `maintenance_due`

---

## 6. Baseline Model Results

Five baseline machine-learning models were evaluated:

* Logistic Regression
* Decision Tree
* Random Forest
* LightGBM
* XGBoost

| Model               | Accuracy | Macro F1 | Critical Recall |
| ------------------- | -------: | -------: | --------------: |
| Logistic Regression |   0.5640 |   0.4821 |          0.5000 |
| Decision Tree       |   0.7020 |   0.6090 |          0.3984 |
| Random Forest       |   0.7575 |   0.6642 |          0.4062 |
| LightGBM            |   0.7830 |   0.7012 |          0.5391 |
| XGBoost             |   0.7740 |   0.6666 |          0.3516 |

These results established baseline performance for the selected models.

---

## 7. Hyperparameter Tuning

Hyperparameter tuning was performed for LightGBM, XGBoost, and Random Forest.

### 7.1 Tuned Model Results

| Model         | Accuracy | Macro Precision | Macro Recall | Macro F1 |  Weighted F1 | Critical Recall |
| ------------- | -------: | --------------: | -----------: | -------: | -----------: | --------------: |
| LightGBM      |   0.8275 |          0.7788 |       0.6923 |   0.7198 |       0.8202 |          0.3750 |
| XGBoost       |   0.8115 |    Not recorded | Not recorded |   0.7052 | Not recorded |          0.3672 |
| Random Forest |   0.7710 |    Not recorded | Not recorded |   0.6801 | Not recorded |          0.4844 |

LightGBM achieved the highest recorded tuned-model Macro F1 among the three tuned models.

However, critical-class recall remained limited, which motivated the class-imbalance and threshold experiments.

---

## 8. SMOTE Experiments

SMOTE experiments were conducted to investigate whether synthetic oversampling could improve the detection of the minority critical class.

### 8.1 LightGBM Results

| Configuration     | CV Macro F1 | Test Accuracy | Test Macro F1 | Critical Recall |
| ----------------- | ----------: | ------------: | ------------: | --------------: |
| No SMOTE          |      0.6998 |        0.8320 |        0.7143 |          0.3516 |
| SMOTE Full        |      0.7013 |        0.8205 |        0.7059 |          0.3828 |
| Critical Class 2x |      0.7041 |        0.8320 |        0.7212 |          0.3750 |
| Critical Class 3x |      0.7056 |        0.8320 |        0.7192 |          0.3828 |

SMOTE improved some critical-class recall values, but the improvement was not sufficient to resolve the minority-class detection problem.

The `SMOTE_Critical_2x` LightGBM configuration was selected as the candidate for threshold experimentation because it achieved a strong Macro F1 score.

---

## 9. Threshold Optimization

The default classification rule assigns the class with the highest predicted probability.

Because the critical class is important for maintenance monitoring, lower critical-class probability thresholds were investigated.

### 9.1 Exploratory Threshold Results

| Critical Threshold | Accuracy | Macro F1 | Critical Precision | Critical Recall |
| -----------------: | -------: | -------: | -----------------: | --------------: |
|               0.10 |   0.7985 |   0.6971 |             0.3744 |          0.5703 |
|               0.15 |   0.8110 |   0.7086 |             0.4231 |          0.5156 |
|               0.20 |   0.8170 |   0.7151 |             0.4599 |          0.4922 |
|               0.30 |   0.8225 |   0.7192 |             0.5000 |          0.4609 |
|               0.45 |   0.8300 |   0.7221 |             0.5930 |          0.3984 |
|               0.50 |   0.8320 |   0.7212 |       Not recorded |          0.3750 |

Lowering the threshold increased critical-class recall but reduced accuracy and critical-class precision.

---

## 10. Validation-Based Threshold Selection

To avoid selecting the threshold solely on the evaluation dataset, a validation split was created from the training data.

The threshold-selection process used:

* Model-training subset: 6,400 rows
* Validation subset: 1,600 rows
* Minimum target critical recall: 0.45

The threshold of **0.10** was selected because it was the only tested threshold that met the minimum critical-recall target on the validation split.

### 10.1 Final Model Evaluation

The final model used:

* LightGBM
* Critical-class-focused SMOTE
* Critical-class threshold: `0.10`

| Metric             | Result |
| ------------------ | -----: |
| Accuracy           | 0.7985 |
| Macro Precision    | 0.6932 |
| Macro Recall       | 0.7262 |
| Macro F1           | 0.6971 |
| Weighted F1        | 0.8001 |
| Critical Precision | 0.3744 |
| Critical Recall    | 0.5703 |

### 10.2 Confusion Matrix

| Actual / Predicted | Normal | Warning | Critical |
| ------------------ | -----: | ------: | -------: |
| Normal             |    941 |      46 |       22 |
| Warning            |    180 |     583 |      100 |
| Critical           |     24 |      31 |       73 |

The selected threshold detected 73 of the 128 critical test cases.

The threshold of 0.10 is an operating-point choice that prioritizes critical-class recall. It is not an objectively optimal threshold for every deployment scenario.

---

## 11. SHAP Explainability

SHAP was used to explain the behaviour of the final LightGBM model.

The analysis generated:

* Global feature-importance data
* Critical-class feature-importance data
* Critical-class bar plot
* Critical-class summary plot
* Local explanation for a selected critical prediction
* Top-20 critical-class feature list

### 11.1 Most Influential Features

The strongest features influencing critical-class predictions were:

1. `Rotational_speed_rpm`
2. `Torque_Nm`
3. `Torque_Nm_rolling_max`
4. `temperature_difference`
5. `Air_temperature_K_rolling_std`
6. `Rotational_speed_rpm_rolling_std`
7. `Rotational_speed_rpm_change`
8. `Process_temperature_K_rolling_std`
9. `Process_temperature_K`
10. `Air_temperature_K`

### 11.2 SHAP Interpretation

The model relies substantially on:

* Rotational speed
* Torque
* Temperature differences
* Rolling maximum torque
* Operating-condition variability
* Changes in rotational speed and torque

SHAP importance indicates which variables influence model predictions. It does not establish that these variables directly cause machine failure.

---

## 12. Project Limitations

### 12.1 Synthetic External Context

The external context variables are synthetic or derived and are not independently measured operational data.

### 12.2 Rule-Based Target

The target variable `Machine_Status_Code` was created using predefined rules rather than independently verified maintenance labels.

### 12.3 Rolling-Feature Interpretation

Rolling features are based on row order. The dataset does not establish that the rows represent a confirmed chronological machine time series.

### 12.4 Evaluation Dataset Usage

The evaluation dataset was used during previous experiments. Therefore, it should not be described as a completely untouched final holdout dataset.

### 12.5 Critical-Class Precision

The selected threshold improves critical-class recall but produces a lower critical-class precision. This may lead to additional false alarms in a real maintenance system.

---

## 13. Future Scope

Potential future improvements include:

1. Collecting real sensor time-series data.
2. Using independently verified maintenance and failure records.
3. Validating the model on a completely untouched external dataset.
4. Adding time-aware train-validation-test splitting.
5. Evaluating cost-sensitive learning methods.
6. Comparing additional imbalance-handling techniques.
7. Calibrating model probabilities.
8. Optimizing the threshold using real maintenance costs.
9. Developing a real-time monitoring dashboard.
10. Integrating maintenance alerts with an industrial monitoring system.
11. Performing model drift monitoring.
12. Validating SHAP explanations with domain experts.

---

## 14. Final Conclusion

This project developed a three-class predictive maintenance classification pipeline using machine-learning models and engineered machine-operating features.

LightGBM produced strong overall classification performance during model development. Class-imbalance experiments and threshold optimization were then used to investigate critical-class detection.

The final selected operating point used a critical-class threshold of `0.10`, achieving a critical-class recall of `0.5703` on the evaluation dataset, alongside an overall accuracy of `0.7985`.

The SHAP analysis showed that rotational speed, torque, temperature-related variables, and operating-condition variability were the most influential features in the model's critical-class predictions.

The system provides a foundation for further development, but real-world deployment requires independently labelled data, temporal validation, external testing, and maintenance-cost-based threshold selection.