from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class PredictionInput(BaseModel):
    machine_id: int
    air_temperature: float = Field(..., description="Air temperature in Kelvin")
    process_temperature: float = Field(..., description="Process temperature in Kelvin")
    rotational_speed: float = Field(..., description="Rotational speed in RPM")
    torque: float = Field(..., description="Torque in Nm")
    tool_wear: float = Field(..., description="Tool wear time in minutes")

class AnalysisRow(BaseModel):
    parameter: str
    current: str
    normal: str
    status: str
    effect: str

class RootCauseAnalysis(BaseModel):
    risk_score: float
    diagnosis: str
    causes: List[str]
    components: List[str]
    maintenance: List[str]
    analysis_table: List[Dict[str, Any]]

class ClassProbabilities(BaseModel):
    normal: float
    warning: float
    critical: float

class PredictionRunResponse(BaseModel):
    id: int
    machine_id: int
    machine_code: str
    machine_name: str
    prediction: str
    predicted_class: Optional[int] = 0
    is_failure: bool
    is_warning: Optional[bool] = False
    failure_probability: float
    machine_health: float
    risk_level: str
    suggested_machine_status: str
    ticket_created: bool
    ticket_priority: Optional[str] = None
    model_version: Optional[str] = "LightGBM_No_SMOTE_Final v4.2"
    class_probabilities: Optional[ClassProbabilities] = None
    root_cause_analysis: RootCauseAnalysis
    predicted_at: datetime

class PredictionHistoryOut(BaseModel):
    id: int
    machine_id: int
    machine_code: Optional[str] = None
    machine_name: Optional[str] = None
    air_temperature: float
    process_temperature: float
    rotational_speed: float
    torque: float
    tool_wear: float
    prediction: str
    probability: float
    confidence: Optional[float] = None
    predicted_at: datetime

    model_config = ConfigDict(from_attributes=True)
