"""
Inference Engine for PredictCNC
Encapsulates model loading, validation, multi-class inference, and Root Cause Analysis (RCA).
Authoritative Model: LightGBM_No_SMOTE_Final.joblib.
"""
import os
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional
from ml.src.feature_engineering import engineer_features_44, create_feature_dataframe_44, MODEL_FEATURES_44

# Authoritative class labels
CLASS_LABELS = {
    0: "Normal Operation",
    1: "Warning / Anomaly Alert",
    2: "Critical Machine Failure"
}

class Predictor:
    """
    PredictCNC ML Inference Engine for LightGBM_No_SMOTE_Final.joblib.
    """
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Predictor, cls).__new__(cls)
            cls._instance._load_model()
        return cls._instance

    def _load_model(self):
        if self._model is not None:
            return
        
        current_path = Path(__file__).resolve()
        # Search parent directories for models folder
        models_dir = None
        for p in [current_path.parent, *current_path.parents]:
            candidate_models = p / "models"
            if candidate_models.exists() and candidate_models.is_dir():
                models_dir = candidate_models
                break
                
        if models_dir is None:
            # Fallback relative to project structure
            models_dir = current_path.parents[2] / "models"

        candidates = [
            models_dir / "LightGBM_No_SMOTE_Final.joblib",
            models_dir / "final_models" / "LightGBM_No_SMOTE_Final.joblib",
            models_dir / "final_lightgbm_model.pkl",
        ]
        
        model_path = None
        for cand in candidates:
            if cand.exists():
                model_path = cand
                break
                
        if model_path is None:
            raise FileNotFoundError(f"Authoritative model artifact not found in candidates: {[str(c) for c in candidates]}")

        self._model = joblib.load(str(model_path))
        self.model_version = "LightGBM_No_SMOTE_Final v4.2"
        self.features_count = len(MODEL_FEATURES_44)

    def predict(
        self,
        air_temp: float,
        process_temp: float,
        rotational_speed: float,
        torque: float,
        tool_wear: float,
        machine_type: str = "L",
        shift: str = "Morning",
        humidity: float = 60.0,
        rolling_history: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Runs multi-class inference and generates root-cause telemetry diagnosis.
        """
        if self._model is None:
            self._load_model()
        # 1. Feature Engineering
        feats = engineer_features_44(
            air_temp=air_temp,
            process_temp=process_temp,
            rotational_speed=rotational_speed,
            torque=torque,
            tool_wear=tool_wear,
            machine_type=machine_type,
            shift=shift,
            humidity=humidity,
            rolling_history=rolling_history
        )
        X = create_feature_dataframe_44(feats)

        # 2. Inference & Multi-Class Probability
        pred_class = int(self._model.predict(X)[0])
        probabilities = self._model.predict_proba(X)[0]  # shape: (3,)

        prob_normal = float(probabilities[0])
        prob_warning = float(probabilities[1])
        prob_critical = float(probabilities[2])

        # Combined risk probability (Class 1 + Class 2)
        failure_prob = float((prob_warning * 0.5 + prob_critical) * 100.0)
        failure_prob = min(100.0, max(0.0, failure_prob))
        health_score = round(max(0.0, 100.0 - failure_prob), 1)

        is_failure = pred_class == 2
        is_warning = pred_class == 1

        if is_failure:
            prediction_label = "Machine Failure"
            risk_level = "High"
            suggested_status = "Critical"
        elif is_warning or failure_prob > 25.0:
            prediction_label = "Warning / Anomaly Alert"
            risk_level = "Medium"
            suggested_status = "Warning"
        else:
            prediction_label = "Normal Operation"
            risk_level = "Low"
            suggested_status = "Healthy"

        # 3. Root Cause Analysis (RCA)
        rca = self._generate_rca(
            air_temp=air_temp,
            process_temp=process_temp,
            rotational_speed=rotational_speed,
            torque=torque,
            tool_wear=tool_wear,
            pred_class=pred_class,
            prob_critical=prob_critical,
            prob_warning=prob_warning
        )

        return {
            "prediction": prediction_label,
            "predicted_class": pred_class,
            "class_label": CLASS_LABELS.get(pred_class, "Unknown"),
            "is_failure": is_failure,
            "is_warning": is_warning,
            "failure_probability": round(failure_prob, 2),
            "machine_health": health_score,
            "risk_level": risk_level,
            "suggested_machine_status": suggested_status,
            "model_version": self.model_version,
            "class_probabilities": {
                "normal": round(prob_normal * 100.0, 2),
                "warning": round(prob_warning * 100.0, 2),
                "critical": round(prob_critical * 100.0, 2),
            },
            "root_cause_analysis": rca
        }

    def _generate_rca(
        self,
        air_temp: float,
        process_temp: float,
        rotational_speed: float,
        torque: float,
        tool_wear: float,
        pred_class: int,
        prob_critical: float,
        prob_warning: float
    ) -> Dict[str, Any]:
        """
        Physics-based root cause analysis matching 44-feature sensor boundaries.
        """
        causes = []
        components = []
        maintenance = []
        analysis_table = []

        temp_diff = process_temp - air_temp

        # Parameter 1: Spindle Speed
        if rotational_speed < 1200 or rotational_speed > 2800:
            status = "Abnormal"
            effect = "Spindle instability / excessive rotational drag"
            causes.append("Rotational speed outside standard envelope (1200-2800 RPM)")
            components.append("Main Drive Spindle & Inverter Drive")
            maintenance.append("Inspect VFD drive parameters and spindle bearing lubrication")
        else:
            status = "Normal"
            effect = "Rotational dynamics stable"
        analysis_table.append({
            "parameter": "Rotational Speed",
            "current": f"{rotational_speed:.1f} RPM",
            "normal": "1200 - 2800 RPM",
            "status": status,
            "effect": effect
        })

        # Parameter 2: Torque
        if torque > 60.0 or torque < 5.0:
            status = "Abnormal"
            effect = "High mechanical strain on cutter head / gear train"
            causes.append("Extreme torque loading exceeding 60 Nm threshold")
            components.append("Gearbox / Chuck Assembly / Cutter Head")
            maintenance.append("Reduce feed rate and verify workpiece clamping tension")
        else:
            status = "Normal"
            effect = "Torque transmission nominal"
        analysis_table.append({
            "parameter": "Torque",
            "current": f"{torque:.1f} Nm",
            "normal": "10.0 - 60.0 Nm",
            "status": status,
            "effect": effect
        })

        # Parameter 3: Thermal Differential
        if temp_diff > 12.0 or temp_diff < 5.0:
            status = "Abnormal"
            effect = "Poor heat dissipation / localized thermal runaway"
            causes.append("Thermal differential Delta-T > 12.0 K indicates cooling inefficiency")
            components.append("Coolant Pump, Heat Exchanger & Thermal Sensors")
            maintenance.append("Flush coolant lines and top up cutting fluid reservoir")
        else:
            status = "Normal"
            effect = "Thermal equilibrium maintained"
        analysis_table.append({
            "parameter": "Thermal Differential (Delta-T)",
            "current": f"{temp_diff:.1f} K",
            "normal": "6.0 - 11.5 K",
            "status": status,
            "effect": effect
        })

        # Parameter 4: Tool Wear
        if tool_wear >= 200.0:
            status = "Critical"
            effect = "Flank wear threshold reached; imminent tool breakage"
            causes.append("Tool wear >= 200 min exceeded tool lifespan")
            components.append("Carbide Insert / Cutting Tool Assembly")
            maintenance.append("Schedule immediate tool insert replacement (T-Index #1)")
        elif tool_wear >= 150.0:
            status = "Warning"
            effect = "Approaching end of tool life"
            maintenance.append("Prepare replacement cutting tool for next changeover")
        else:
            status = "Normal"
            effect = "Cutting edge sharp and intact"
        analysis_table.append({
            "parameter": "Tool Wear",
            "current": f"{tool_wear:.1f} min",
            "normal": "< 150.0 min",
            "status": status,
            "effect": effect
        })

        if not causes and pred_class == 0:
            diagnosis = "All physical telemetry parameters are operating well within nominal manufacturing tolerances."
        elif pred_class == 1:
            diagnosis = "Warning: Moderate telemetry anomaly detected. Early thermal or mechanical drift observed."
        else:
            diagnosis = "Critical Alert: High probability of imminent mechanical failure. Immediate intervention recommended."

        return {
            "risk_score": round((prob_warning * 0.4 + prob_critical * 0.9) * 100.0, 1),
            "diagnosis": diagnosis,
            "causes": causes if causes else ["Telemetry operating in nominal regime"],
            "components": list(set(components)) if components else ["All assemblies verified nominal"],
            "maintenance": maintenance if maintenance else ["Maintain standard preventative schedule"],
            "analysis_table": analysis_table
        }

__all__ = ["Predictor", "CLASS_LABELS"]
