from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from src.database.session import get_db
from src.schemas.machine import MachineOut, MachineCreate, MachineUpdate
from src.services.machine_service import MachineService

router = APIRouter()

@router.get("", response_model=List[MachineOut])
def get_machines(
    search: Optional[str] = Query(None, description="Search keyword for machine code, name, dept"),
    department: Optional[str] = Query(None, description="Filter by department"),
    status: Optional[str] = Query(None, description="Filter by status (Healthy, Warning, Critical)"),
    db: Session = Depends(get_db)
):
    return MachineService.get_all(db, search=search, department=department, status=status)

@router.get("/{machine_id}", response_model=MachineOut)
def get_machine(machine_id: int, db: Session = Depends(get_db)):
    machine = MachineService.get_by_id(db, machine_id)
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    return machine

@router.post("", response_model=MachineOut, status_code=status.HTTP_201_CREATED)
def create_machine(data: MachineCreate, db: Session = Depends(get_db)):
    return MachineService.create(db, data)

@router.put("/{machine_id}", response_model=MachineOut)
def update_machine(machine_id: int, data: MachineUpdate, db: Session = Depends(get_db)):
    machine = MachineService.update(db, machine_id, data)
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    return machine

@router.delete("/{machine_id}")
def delete_machine(machine_id: int, db: Session = Depends(get_db)):
    success = MachineService.delete(db, machine_id)
    if not success:
        raise HTTPException(status_code=404, detail="Machine not found")
    return {"message": f"Machine #{machine_id} deleted successfully"}
