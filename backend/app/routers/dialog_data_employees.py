import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.dialog_data_employee import (
    DialogDataEmployeeCreate, DialogDataEmployeeUpdate, DialogDataEmployeeOut, DialogDataConnectionCreate,
)
from app.services import dialog_data_employee_service

router = APIRouter(prefix="/dialog-data/employees", tags=["dialog-data-employees"])


@router.get("", response_model=list[DialogDataEmployeeOut])
def list_employees(search: str | None = Query(None), db: Session = Depends(get_db)):
    return dialog_data_employee_service.list_employees(db, search=search)


@router.post("", response_model=DialogDataEmployeeOut, status_code=201)
def create_employee(payload: DialogDataEmployeeCreate, db: Session = Depends(get_db)):
    return dialog_data_employee_service.create_employee(db, payload)


@router.put("/{employee_id}", response_model=DialogDataEmployeeOut)
def update_employee(employee_id: uuid.UUID, payload: DialogDataEmployeeUpdate, db: Session = Depends(get_db)):
    return dialog_data_employee_service.update_employee(db, employee_id, payload)


@router.delete("/{employee_id}", response_model=DialogDataEmployeeOut)
def delete_employee(employee_id: uuid.UUID, db: Session = Depends(get_db)):
    return dialog_data_employee_service.soft_delete_employee(db, employee_id)


@router.post("/{employee_id}/connections", response_model=DialogDataEmployeeOut, status_code=201)
def add_connection(employee_id: uuid.UUID, payload: DialogDataConnectionCreate, db: Session = Depends(get_db)):
    return dialog_data_employee_service.add_connection(db, employee_id, payload)


@router.delete("/connections/{connection_id}", status_code=204)
def remove_connection(connection_id: uuid.UUID, db: Session = Depends(get_db)):
    dialog_data_employee_service.remove_connection(db, connection_id)