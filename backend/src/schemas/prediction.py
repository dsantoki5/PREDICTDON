from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class PredictionInput(BaseModel):
    machine_id: int = Field(..., description="ID of the registered CNC machine")
    air_temperature: float = Field(..., ge=250.0, le=350.0, description="Air temperature in Kelvin")
    process_temperature: float = Field(..., ge=250.0, le=350.0, description="Process temperature in Kelvin")
    rotational_speed: float = Field(..., ge=500.0, le=5000.0, description="Spindle speed in RPM")
    torque: float = Field(..., ge=0.0, le=200.0, description="Torque in Nm")
    tool_wear: float = Field(..., ge=0.0, le=500.0, description="Tool wear time in minutes")

class PredictionResponse(BaseModel):
    id: Optional[int] = None
    machine_id: int
    prediction: str
    is_failure: bool
    failure_probability: float
    machine_health: float
    risk_level: str
    suggested_machine_status: str
    ticket_created: bool
    ticket_priority: Optional[str] = None
    root_cause_analysis: Dict[str, Any]
