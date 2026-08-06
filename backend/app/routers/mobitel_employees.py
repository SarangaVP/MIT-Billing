import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.mobitel_employee import MobitelEmployeeCreate, MobitelEmployeeUpdate, MobitelEmployeeOut
from app.services import mobitel_employee_service

router = APIRouter(prefix="/mobitel/employees", tags=["mobitel-employees"])


@router.get("", response_model=list[MobitelEmployeeOut])
def list_employees(search: str | None = Query(None), lob: str | None = None, db: Session = Depends(get_db)):
    return mobitel_employee_service.list_employees(db, search=search, lob=lob)


@router.post("", response_model=MobitelEmployeeOut, status_code=201)
def create_employee(payload: MobitelEmployeeCreate, db: Session = Depends(get_db)):
    return mobitel_employee_service.create_employee(db, payload)


@router.put("/{employee_id}", response_model=MobitelEmployeeOut)
def update_employee(employee_id: uuid.UUID, payload: MobitelEmployeeUpdate, db: Session = Depends(get_db)):
    return mobitel_employee_service.update_employee(db, employee_id, payload)


@router.delete("/{employee_id}", response_model=MobitelEmployeeOut)
def delete_employee(employee_id: uuid.UUID, db: Session = Depends(get_db)):
    return mobitel_employee_service.soft_delete_employee(db, employee_id)