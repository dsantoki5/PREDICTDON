from fastapi import APIRouter
from src.api.v1.endpoints import auth, health, machines, predictions, maintenance, reports, dashboard

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(machines.router, prefix="/machines", tags=["Machines"])
api_router.include_router(predictions.router, prefix="/predictions", tags=["Predictions"])
api_router.include_router(maintenance.router, prefix="/maintenance", tags=["Maintenance"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])

