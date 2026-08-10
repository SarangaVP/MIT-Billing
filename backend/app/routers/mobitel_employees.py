import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.mobitel_employee import (
    MobitelEmployeeCreate, MobitelEmployeeUpdate, MobitelEmployeeOut, MobitelConnectionCreate,
)
from app.services import mobitel_employee_service

router = APIRouter(prefix="/mobitel/employees", tags=["mobitel-employees"])


@router.get("", response_model=list[MobitelEmployeeOut])
def list_employees(search: str | None = Query(None), db: Session = Depends(get_db)):
    return mobitel_employee_service.list_employees(db, search=search)


@router.post("", response_model=MobitelEmployeeOut, status_code=201)
def create_employee(payload: MobitelEmployeeCreate, db: Session = Depends(get_db)):
    return mobitel_employee_service.create_employee(db, payload)


@router.put("/{employee_id}", response_model=MobitelEmployeeOut)
def update_employee(employee_id: uuid.UUID, payload: MobitelEmployeeUpdate, db: Session = Depends(get_db)):
    return mobitel_employee_service.update_employee(db, employee_id, payload)


@router.delete("/{employee_id}", response_model=MobitelEmployeeOut)
def delete_employee(employee_id: uuid.UUID, db: Session = Depends(get_db)):
    return mobitel_employee_service.soft_delete_employee(db, employee_id)


@router.post("/{employee_id}/connections", response_model=MobitelEmployeeOut, status_code=201)
def add_connection(employee_id: uuid.UUID, payload: MobitelConnectionCreate, db: Session = Depends(get_db)):
    return mobitel_employee_service.add_connection(db, employee_id, payload)


@router.delete("/connections/{connection_id}", status_code=204)
def remove_connection(connection_id: uuid.UUID, db: Session = Depends(get_db)):
    mobitel_employee_service.remove_connection(db, connection_id)