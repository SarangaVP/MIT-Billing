import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeOut
from app.schemas.mobile_number import MobileNumberCreate, MobileNumberOut
from app.services import employee_service

router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("", response_model=list[EmployeeOut])
def list_employees(search: str | None = Query(None), lob: str | None = None, include_deleted: bool = False, db: Session = Depends(get_db)):
    return employee_service.list_employees(db, search=search, lob=lob, include_deleted=include_deleted)


@router.post("", response_model=EmployeeOut, status_code=201)
def create_employee(payload: EmployeeCreate, db: Session = Depends(get_db)):
    return employee_service.create_employee(db, payload)


@router.get("/{employee_id}", response_model=EmployeeOut)
def get_employee(employee_id: uuid.UUID, db: Session = Depends(get_db)):
    return employee_service.get_employee(db, employee_id)


@router.put("/{employee_id}", response_model=EmployeeOut)
def update_employee(employee_id: uuid.UUID, payload: EmployeeUpdate, db: Session = Depends(get_db)):
    return employee_service.update_employee(db, employee_id, payload)


@router.delete("/{employee_id}", response_model=EmployeeOut)
def delete_employee(employee_id: uuid.UUID, db: Session = Depends(get_db)):
    return employee_service.soft_delete_employee(db, employee_id)


@router.post("/{employee_id}/mobile-numbers", response_model=MobileNumberOut, status_code=201)
def add_mobile_number(employee_id: uuid.UUID, payload: MobileNumberCreate, db: Session = Depends(get_db)):
    return employee_service.add_mobile_number(db, employee_id, payload)


@router.delete("/{employee_id}/mobile-numbers/{number_id}", response_model=MobileNumberOut)
def remove_mobile_number(employee_id: uuid.UUID, number_id: uuid.UUID, db: Session = Depends(get_db)):
    return employee_service.remove_mobile_number(db, employee_id, number_id)