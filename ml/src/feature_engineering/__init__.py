"""
Feature Engineering Pipeline for PredictCNC
Encapsulates domain-specific physical transformations for CNC telemetry.
Produces the authoritative 44 input features expected by LightGBM_No_SMOTE_Final.joblib.
"""
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

MODEL_FEATURES_44 = [
    'Air_temperature_K',
    'Process_temperature_K',
    'Rotational_speed_rpm',
    'Torque_Nm',
    'Air_temperature_K_rolling_mean',
    'Air_temperature_K_rolling_std',
    'Air_temperature_K_rolling_min',
    'Air_temperature_K_rolling_max',
    'Air_temperature_K_change',
    'Process_temperature_K_rolling_mean',
    'Process_temperature_K_rolling_std',
    'Process_temperature_K_rolling_min',
    'Process_temperature_K_rolling_max',
    'Process_temperature_K_change',
    'Rotational_speed_rpm_rolling_mean',
    'Rotational_speed_rpm_rolling_std',
    'Rotational_speed_rpm_rolling_min',
    'Rotational_speed_rpm_rolling_max',
    'Rotational_speed_rpm_change',
    'Torque_Nm_rolling_mean',
    'Torque_Nm_rolling_std',
    'Torque_Nm_rolling_min',
    'Torque_Nm_rolling_max',
    'Torque_Nm_change',
    'temperature_difference',
    'power_consumption',
    'load_signal',
    'ambient_temperature',
    'load_density',
    'humidity',
    'maintenance_due',
    'shift_Morning',
    'shift_Night',
    'ambient_difference',
    'load_stress',
    'load_density_interaction',
    'temperature_humidity_interaction',
    'torque_speed_ratio',
    'maintenance_load_interaction',
    'rpm_std_10',
    'torque_std_10',
    'load_density_mean_10',
    'Type_L',
    'Type_M'
]

def engineer_features_44(
    air_temp: float,
    process_temp: float,
    rotational_speed: float,
    torque: float,
    tool_wear: float,
    machine_type: str = 'L',
    shift: str = 'Morning',
    humidity: float = 60.0,
    rolling_history: Optional[Dict[str, Any]] = None
) -> Dict[str, float]:
    """
    Computes exactly the 44 features required by the LightGBM multi-class model.
    """
    # 1. Physics domain features
    temp_diff = float(process_temp - air_temp)
    power = float((2 * np.pi * rotational_speed * torque) / 60.0)
    load_density = float(torque / 100.0)
    load_signal = float(torque * (rotational_speed / 1000.0))
    load_stress = float(torque * load_density)
    torque_speed_ratio = float(torque / (rotational_speed + 1e-6))
    ambient_temp = float(air_temp - 273.15)
    ambient_diff = temp_diff
    maint_due = 1.0 if tool_wear >= 180.0 else 0.0
    maint_load_inter = float(maint_due * torque)
    temp_hum_inter = float(temp_diff * (humidity / 100.0))
    load_density_inter = float(load_density * load_stress)

    # 2. Machine Type One-Hot Encoding
    type_upper = (machine_type or 'L').upper()
    type_l = 1.0 if type_upper == 'L' else 0.0
    type_m = 1.0 if type_upper == 'M' else 0.0

    # 3. Shift One-Hot Encoding
    shift_title = (shift or 'Morning').capitalize()
    shift_morning = 1.0 if shift_title == 'Morning' else 0.0
    shift_night = 1.0 if shift_title == 'Night' else 0.0

    # 4. Rolling statistics (from historical window or sensor deviation)
    h = rolling_history or {}
    air_mean = float(h.get('air_temp_mean', air_temp))
    air_std = float(h.get('air_temp_std', 0.2))
    air_min = float(h.get('air_temp_min', air_temp - 0.5))
    air_max = float(h.get('air_temp_max', air_temp + 0.5))
    air_change = float(air_temp - air_mean)

    proc_mean = float(h.get('proc_temp_mean', process_temp))
    proc_std = float(h.get('proc_temp_std', 0.25))
    proc_min = float(h.get('proc_temp_min', process_temp - 0.5))
    proc_max = float(h.get('proc_temp_max', process_temp + 0.5))
    proc_change = float(process_temp - proc_mean)

    rpm_mean = float(h.get('rpm_mean', rotational_speed))
    rpm_std = float(h.get('rpm_std', 12.0))
    rpm_min = float(h.get('rpm_min', rotational_speed - 25.0))
    rpm_max = float(h.get('rpm_max', rotational_speed + 25.0))
    rpm_change = float(rotational_speed - rpm_mean)

    torque_mean = float(h.get('torque_mean', torque))
    torque_std = float(h.get('torque_std', 1.5))
    torque_min = float(h.get('torque_min', torque - 3.0))
    torque_max = float(h.get('torque_max', torque + 3.0))
    torque_change = float(torque - torque_mean)

    return {
        'Air_temperature_K': float(air_temp),
        'Process_temperature_K': float(process_temp),
        'Rotational_speed_rpm': float(rotational_speed),
        'Torque_Nm': float(torque),
        'Air_temperature_K_rolling_mean': air_mean,
        'Air_temperature_K_rolling_std': air_std,
        'Air_temperature_K_rolling_min': air_min,
        'Air_temperature_K_rolling_max': air_max,
        'Air_temperature_K_change': air_change,
        'Process_temperature_K_rolling_mean': proc_mean,
        'Process_temperature_K_rolling_std': proc_std,
        'Process_temperature_K_rolling_min': proc_min,
        'Process_temperature_K_rolling_max': proc_max,
        'Process_temperature_K_change': proc_change,
        'Rotational_speed_rpm_rolling_mean': rpm_mean,
        'Rotational_speed_rpm_rolling_std': rpm_std,
        'Rotational_speed_rpm_rolling_min': rpm_min,
        'Rotational_speed_rpm_rolling_max': rpm_max,
        'Rotational_speed_rpm_change': rpm_change,
        'Torque_Nm_rolling_mean': torque_mean,
        'Torque_Nm_rolling_std': torque_std,
        'Torque_Nm_rolling_min': torque_min,
        'Torque_Nm_rolling_max': torque_max,
        'Torque_Nm_change': torque_change,
        'temperature_difference': temp_diff,
        'power_consumption': power,
        'load_signal': load_signal,
        'ambient_temperature': ambient_temp,
        'load_density': load_density,
        'humidity': float(humidity),
        'maintenance_due': maint_due,
        'shift_Morning': shift_morning,
        'shift_Night': shift_night,
        'ambient_difference': ambient_diff,
        'load_stress': load_stress,
        'load_density_interaction': load_density_inter,
        'temperature_humidity_interaction': temp_hum_inter,
        'torque_speed_ratio': torque_speed_ratio,
        'maintenance_load_interaction': maint_load_inter,
        'rpm_std_10': rpm_std,
        'torque_std_10': torque_std,
        'load_density_mean_10': load_density,
        'Type_L': type_l,
        'Type_M': type_m,
    }

def create_feature_dataframe_44(features_dict: Dict[str, float]) -> pd.DataFrame:
    """
    Constructs a DataFrame guaranteeing the exact 44-feature schema and column ordering.
    """
    ordered_data = {feat: [float(features_dict[feat])] for feat in MODEL_FEATURES_44}
    return pd.DataFrame(ordered_data)

__all__ = [
    'MODEL_FEATURES_44',
    'engineer_features_44',
    'create_feature_dataframe_44'
]
