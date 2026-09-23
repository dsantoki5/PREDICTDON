"""
Inference Engine for PredictCNC (Compatibility Module)
Re-exports Predictor and CLASS_LABELS from ml.src.inference package.
"""
from ml.src.inference import Predictor, CLASS_LABELS

__all__ = ["Predictor", "CLASS_LABELS"]
