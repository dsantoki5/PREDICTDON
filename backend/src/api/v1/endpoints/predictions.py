from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from src.database.session import get_db
from src.schemas.prediction import PredictionInput, PredictionRunResponse, PredictionHistoryOut
from src.services.prediction_service import PredictionService

router = APIRouter()

@router.post("/run", response_model=PredictionRunResponse)
def run_prediction(payload: PredictionInput, db: Session = Depends(get_db)):
    try:
        return PredictionService.run_prediction(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")

@router.get("/history", response_model=List[PredictionHistoryOut])
def get_history(
    machine_id: Optional[int] = Query(None, description="Filter history by machine ID"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    return PredictionService.get_history(db, machine_id=machine_id, limit=limit, offset=offset)

@router.delete("/history/{item_id}")
def delete_history_item(item_id: int, db: Session = Depends(get_db)):
    success = PredictionService.delete_history_item(db, item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Prediction history record not found")
    return {"message": f"Prediction record #{item_id} deleted"}
