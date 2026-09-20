from pydantic import BaseModel

class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    ml_engine: str
