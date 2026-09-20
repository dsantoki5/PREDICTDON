from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from src.models.machine import Machine
from src.models.maintenance import MaintenanceTicket
from src.schemas.maintenance import MaintenanceUpdate

class MaintenanceService:
    @staticmethod
    def get_all(
        db: Session,
        status: Optional[str] = None,
        priority: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        query = (
            db.query(
                MaintenanceTicket,
                Machine.machine_code,
                Machine.machine_name
            )
            .join(Machine, MaintenanceTicket.machine_id == Machine.id)
        )
        if status:
            query = query.filter(MaintenanceTicket.status == status)
        if priority:
            query = query.filter(MaintenanceTicket.priority == priority)

        rows = query.order_by(MaintenanceTicket.created_at.desc()).all()
        return [
            {
                "id": t.id,
                "machine_id": t.machine_id,
                "machine_code": code,
                "machine_name": name,
                "prediction_id": t.prediction_id,
                "priority": t.priority,
                "status": t.status,
                "remarks": t.remarks,
                "created_at": t.created_at
            }
            for t, code, name in rows
        ]

    @staticmethod
    def update(db: Session, ticket_id: int, data: MaintenanceUpdate) -> Optional[MaintenanceTicket]:
        ticket = db.query(MaintenanceTicket).filter(MaintenanceTicket.id == ticket_id).first()
        if not ticket:
            return None
        ticket.status = data.status
        if data.remarks is not None:
            ticket.remarks = data.remarks
        db.commit()
        db.refresh(ticket)
        return ticket

    @staticmethod
    def delete(db: Session, ticket_id: int) -> bool:
        ticket = db.query(MaintenanceTicket).filter(MaintenanceTicket.id == ticket_id).first()
        if not ticket:
            return False
        db.delete(ticket)
        db.commit()
        return True
