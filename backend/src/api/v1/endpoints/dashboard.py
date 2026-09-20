from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.database.session import get_db
from src.schemas.reports import DashboardSummaryOut
from src.services.reports_service import ReportsService
from src.services.prediction_service import PredictionService
from src.services.machine_service import MachineService

router = APIRouter()

@router.get("/summary", response_model=DashboardSummaryOut)
def get_dashboard_summary(db: Session = Depends(get_db)):
    rep_summary = ReportsService.get_summary(db)
    recent_preds = PredictionService.get_history(db, limit=5)
    machines = MachineService.get_all(db)
    recent_machines = [
        {
            "id": m.id,
            "machine_code": m.machine_code,
            "machine_name": m.machine_name,
            "department": m.department,
            "status": m.status
        }
        for m in machines[:5]
    ]

    return DashboardSummaryOut(
        total_machines=rep_summary["total_machines"],
        healthy=rep_summary["healthy_machines"],
        warning=rep_summary["warning_machines"],
        critical=rep_summary["critical_machines"],
        total_predictions=rep_summary["total_predictions"],
        normal_predictions=rep_summary["normal_predictions"],
        failure_predictions=rep_summary["failure_predictions"],
        pending_maintenance=rep_summary["pending_tickets"],
        avg_health=rep_summary["avg_health"],
        avg_failure=rep_summary["avg_failure"],
        recent_predictions=recent_preds,
        recent_machines=recent_machines
    )
