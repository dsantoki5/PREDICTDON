import os
import sys
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional

# Ensure project root is in sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from ml.src.inference import Predictor

class MLService:
    """
    Centralized ML Service for backend inference.
    """
    _predictor = None

    @classmethod
    def get_predictor(cls) -> Predictor:
        if cls._predictor is None:
            cls._predictor = Predictor()
        return cls._predictor

    @classmethod
    def validate_inputs(
        cls,
        air_temp: float,
        process_temp: float,
        rotational_speed: float,
        torque: float,
        tool_wear: float
    ) -> None:
        """
        Strict validation of physical sensor inputs.
        Rejects NaNs, Infinities, and absurd out-of-physical-bounds telemetry.
        """
        for name, val in [
            ("air_temperature", air_temp),
            ("process_temperature", process_temp),
            ("rotational_speed", rotational_speed),
            ("torque", torque),
            ("tool_wear", tool_wear)
        ]:
            if val is None or np.isnan(val) or np.isinf(val):
                raise ValueError(f"Invalid sensor telemetry: '{name}' cannot be NaN or Infinite.")

        if air_temp < 250.0 or air_temp > 350.0:
            raise ValueError(f"Air temperature {air_temp} K is outside valid physical range (250K - 350K).")

        if process_temp < 250.0 or process_temp > 370.0:
            raise ValueError(f"Process temperature {process_temp} K is outside valid physical range (250K - 370K).")

        if rotational_speed <= 0 or rotational_speed > 5000.0:
            raise ValueError(f"Rotational speed {rotational_speed} RPM is outside valid spindle range (1 - 5000 RPM).")

        if torque < 0 or torque > 200.0:
            raise ValueError(f"Torque {torque} Nm is outside valid mechanical range (0 - 200 Nm).")

        if tool_wear < 0 or tool_wear > 600.0:
            raise ValueError(f"Tool wear {tool_wear} min is outside valid tool lifespan range (0 - 600 min).")

    @classmethod
    def run_prediction(
        cls,
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
        Executes prediction with full validation.
        """
        cls.validate_inputs(
            air_temp=air_temp,
            process_temp=process_temp,
            rotational_speed=rotational_speed,
            torque=torque,
            tool_wear=tool_wear
        )
        predictor = cls.get_predictor()
        return predictor.predict(
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
