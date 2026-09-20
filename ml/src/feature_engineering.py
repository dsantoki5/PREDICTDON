"""
Feature Engineering Pipeline for PredictCNC
Encapsulates domain-specific physics transformations for CNC telemetry.
"""
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

MODEL_FEATURES = [
    "rpm_torque_interaction",
    "Rotational_speed_rpm",
    "load_stress",
    "Torque_Nm",
    "load_density",
    "Tool_wear_min",
    "temperature_ratio",
    "tool_wear_mean_10",
    "temperature_difference",
    "air_temp_mean_10"
]

def engineer_features(
    air_temp: float,
    process_temp: float,
    rotational_speed: float,
    torque: float,
    tool_wear: float,
    tool_wear_mean_10: Optional[float] = None,
    air_temp_mean_10: Optional[float] = None
) -> Dict[str, float]:
    load_density = torque / 100.0
    rpm_torque_interaction = rotational_speed * torque
    temperature_difference = process_temp - air_temp
    temperature_ratio = process_temp / air_temp if air_temp != 0 else 1.0
    load_stress = torque * load_density

    tool_avg = tool_wear_mean_10 if tool_wear_mean_10 is not None else tool_wear
    air_avg = air_temp_mean_10 if air_temp_mean_10 is not None else air_temp

    return {
        "rpm_torque_interaction": float(rpm_torque_interaction),
        "Rotational_speed_rpm": float(rotational_speed),
        "load_stress": float(load_stress),
        "Torque_Nm": float(torque),
        "load_density": float(load_density),
        "Tool_wear_min": float(tool_wear),
        "temperature_ratio": float(temperature_ratio),
        "tool_wear_mean_10": float(tool_avg),
        "temperature_difference": float(temperature_difference),
        "air_temp_mean_10": float(air_avg),
    }

def create_feature_dataframe(features_dict: Dict[str, float]) -> pd.DataFrame:
    ordered_data = {feat: [features_dict[feat]] for feat in MODEL_FEATURES}
    return pd.DataFrame(ordered_data)
