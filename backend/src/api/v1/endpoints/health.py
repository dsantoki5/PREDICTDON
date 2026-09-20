from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.schemas.health import HealthResponse
from src.database.session import get_db

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return HealthResponse(
        status="operational",
        version="2.0.0",
        database=db_status,
        ml_engine="LightGBM v4 (AI4I 2020 Model)"
    )
