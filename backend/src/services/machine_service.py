from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from src.models.machine import Machine
from src.schemas.machine import MachineCreate, MachineUpdate

class MachineService:
    @staticmethod
    def get_all(
        db: Session,
        search: Optional[str] = None,
        department: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Machine]:
        query = db.query(Machine)
        if search:
            kw = f"%{search}%"
            query = query.filter(
                or_(
                    Machine.machine_code.ilike(kw),
                    Machine.machine_name.ilike(kw),
                    Machine.department.ilike(kw),
                    Machine.manufacturer.ilike(kw)
                )
            )
        if department:
            query = query.filter(Machine.department == department)
        if status:
            query = query.filter(Machine.status == status)
        return query.order_by(Machine.id.asc()).all()

    @staticmethod
    def get_by_id(db: Session, machine_id: int) -> Optional[Machine]:
        return db.query(Machine).filter(Machine.id == machine_id).first()

    @staticmethod
    def create(db: Session, data: MachineCreate) -> Machine:
        machine = Machine(
            machine_code=data.machine_code.strip(),
            machine_name=data.machine_name.strip(),
            department=data.department.strip() if data.department else None,
            manufacturer=data.manufacturer.strip() if data.manufacturer else None,
            installation_date=data.installation_date,
            status=data.status or "Healthy"
        )
        db.add(machine)
        db.commit()
        db.refresh(machine)
        return machine

    @staticmethod
    def update(db: Session, machine_id: int, data: MachineUpdate) -> Optional[Machine]:
        machine = db.query(Machine).filter(Machine.id == machine_id).first()
        if not machine:
            return None
        if data.machine_code is not None:
            machine.machine_code = data.machine_code.strip()
        if data.machine_name is not None:
            machine.machine_name = data.machine_name.strip()
        if data.department is not None:
            machine.department = data.department.strip()
        if data.manufacturer is not None:
            machine.manufacturer = data.manufacturer.strip()
        if data.installation_date is not None:
            machine.installation_date = data.installation_date
        if data.status is not None:
            machine.status = data.status
        db.commit()
        db.refresh(machine)
        return machine

    @staticmethod
    def delete(db: Session, machine_id: int) -> bool:
        machine = db.query(Machine).filter(Machine.id == machine_id).first()
        if not machine:
            return False
        db.delete(machine)
        db.commit()
        return True
