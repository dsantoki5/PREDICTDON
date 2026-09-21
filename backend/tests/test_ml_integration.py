"""
Automated Integration Tests for LightGBM_No_SMOTE_Final.joblib and Backend ML Service.
"""
import pytest
import numpy as np
from src.services.ml_service import MLService
from ml.src.inference import Predictor, CLASS_LABELS
from ml.src.feature_engineering import MODEL_FEATURES_44

def test_model_loading():
    predictor = MLService.get_predictor()
    assert predictor is not None
    assert predictor._model is not None
    assert predictor.features_count == 44
    assert len(MODEL_FEATURES_44) == 44

def test_nominal_prediction():
    res = MLService.run_prediction(
        air_temp=298.1,
        process_temp=308.6,
        rotational_speed=1500.0,
        torque=40.0,
        tool_wear=50.0
    )
    assert "prediction" in res
    assert "predicted_class" in res
    assert res["predicted_class"] in [0, 1, 2]
    assert "class_probabilities" in res
    assert res["class_probabilities"]["normal"] >= 0.0
    assert res["class_probabilities"]["warning"] >= 0.0
    assert res["class_probabilities"]["critical"] >= 0.0
    assert res["machine_health"] >= 0.0
    assert "root_cause_analysis" in res

def test_critical_failure_prediction():
    res = MLService.run_prediction(
        air_temp=304.0,
        process_temp=314.5,
        rotational_speed=1200.0,
        torque=75.0,
        tool_wear=240.0
    )
    assert res["predicted_class"] == 2
    assert res["is_failure"] is True
    assert res["suggested_machine_status"] == "Critical"
    assert res["class_probabilities"]["critical"] > 50.0

def test_input_validation_nan():
    with pytest.raises(ValueError, match="cannot be NaN or Infinite"):
        MLService.run_prediction(
            air_temp=float("nan"),
            process_temp=308.6,
            rotational_speed=1500.0,
            torque=40.0,
            tool_wear=50.0
        )

def test_input_validation_out_of_bounds():
    with pytest.raises(ValueError, match="outside valid physical range"):
        MLService.run_prediction(
            air_temp=500.0,
            process_temp=308.6,
            rotational_speed=1500.0,
            torque=40.0,
            tool_wear=50.0
        )

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
