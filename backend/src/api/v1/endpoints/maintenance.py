from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from src.database.session import get_db
from src.schemas.maintenance import MaintenanceTicketOut, MaintenanceUpdate
from src.services.maintenance_service import MaintenanceService

router = APIRouter()

@router.get("", response_model=List[MaintenanceTicketOut])
def get_tickets(
    status: Optional[str] = Query(None, description="Filter by status (Pending, In Progress, Completed)"),
    priority: Optional[str] = Query(None, description="Filter by priority (High, Medium, Low)"),
    db: Session = Depends(get_db)
):
    return MaintenanceService.get_all(db, status=status, priority=priority)

@router.put("/{ticket_id}", response_model=MaintenanceTicketOut)
def update_ticket(ticket_id: int, data: MaintenanceUpdate, db: Session = Depends(get_db)):
    ticket = MaintenanceService.update(db, ticket_id, data)
    if not ticket:
        raise HTTPException(status_code=404, detail="Maintenance ticket not found")
    # Fetch with joined details
    tickets = MaintenanceService.get_all(db)
    for t in tickets:
        if t["id"] == ticket_id:
            return t
    return ticket

@router.delete("/{ticket_id}")
def delete_ticket(ticket_id: int, db: Session = Depends(get_db)):
    success = MaintenanceService.delete(db, ticket_id)
    if not success:
        raise HTTPException(status_code=404, detail="Maintenance ticket not found")
    return {"message": f"Maintenance ticket #{ticket_id} deleted"}
