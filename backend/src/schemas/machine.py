from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field

class MachineBase(BaseModel):
    machine_code: str = Field(..., max_length=30)
    machine_name: str = Field(..., max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    manufacturer: Optional[str] = Field(None, max_length=100)
    installation_date: Optional[date] = None
    status: Optional[str] = Field("Healthy", max_length=20)

class MachineCreate(MachineBase):
    pass

class MachineUpdate(BaseModel):
    machine_code: Optional[str] = None
    machine_name: Optional[str] = None
    department: Optional[str] = None
    manufacturer: Optional[str] = None
    installation_date: Optional[date] = None
    status: Optional[str] = None

class MachineOut(MachineBase):
    id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
