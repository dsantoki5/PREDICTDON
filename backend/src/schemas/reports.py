from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class DashboardSummaryOut(BaseModel):
    total_machines: int
    healthy: int
    warning: int
    critical: int
    total_predictions: int
    normal_predictions: int
    failure_predictions: int
    pending_maintenance: int
    avg_health: float
    avg_failure: float
    recent_predictions: List[Dict[str, Any]]
    recent_machines: List[Dict[str, Any]]

class ReportsSummaryOut(BaseModel):
    total_predictions: int
    normal_predictions: int
    failure_predictions: int
    pending_tickets: int
    in_progress_tickets: int
    completed_tickets: int
    total_machines: int
    avg_failure: float
    avg_health: float
    highest_failure: float
    lowest_failure: float
    model_metrics: Dict[str, Any]
