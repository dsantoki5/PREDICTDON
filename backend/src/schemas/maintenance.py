from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class MaintenanceUpdate(BaseModel):
    status: str # Pending, In Progress, Completed
    remarks: Optional[str] = None

class MaintenanceTicketOut(BaseModel):
    id: int
    machine_id: int
    machine_code: Optional[str] = None
    machine_name: Optional[str] = None
    prediction_id: Optional[int] = None
    priority: str
    status: str
    remarks: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
