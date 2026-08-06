import uuid

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.mobitel_employee import MobitelEmployee, MobitelEmployeeStatus
from app.schemas.mobitel_employee import MobitelEmployeeCreate, MobitelEmployeeUpdate


def list_employees(db, search=None, lob=None, include_deleted=False):
    query = db.query(MobitelEmployee)
    if not include_deleted:
        query = query.filter(MobitelEmployee.is_deleted.is_(False))
    if lob:
        query = query.filter(MobitelEmployee.lob == lob)
    if search:
        pattern = f"%{search}%"
        query = query.filter(or_(
            MobitelEmployee.name.ilike(pattern),
            MobitelEmployee.emp_no.ilike(pattern),
            MobitelEmployee.mobile_no.ilike(pattern),
        ))
    return query.order_by(MobitelEmployee.name).all()


def get_employee(db: Session, employee_id: uuid.UUID) -> MobitelEmployee:
    employee = db.query(MobitelEmployee).filter(MobitelEmployee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Mobitel employee not found")
    return employee


def create_employee(db: Session, payload: MobitelEmployeeCreate) -> MobitelEmployee:
    existing_emp_no = db.query(MobitelEmployee).filter(
        MobitelEmployee.emp_no == payload.emp_no, MobitelEmployee.is_deleted.is_(False)
    ).first()
    if existing_emp_no:
        raise HTTPException(status_code=409, detail=f"EMP No {payload.emp_no} already exists")

    existing_number = db.query(MobitelEmployee).filter(
        MobitelEmployee.mobile_no == payload.mobile_no, MobitelEmployee.is_deleted.is_(False)
    ).first()
    if existing_number:
        raise HTTPException(
            status_code=409,
            detail=f"Mobile number {payload.mobile_no} is already assigned to {existing_number.name}",
        )

    employee = MobitelEmployee(**payload.model_dump())
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


def update_employee(db: Session, employee_id: uuid.UUID, payload: MobitelEmployeeUpdate) -> MobitelEmployee:
    employee = get_employee(db, employee_id)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(employee, field, value)
    db.commit()
    db.refresh(employee)
    return employee


def soft_delete_employee(db: Session, employee_id: uuid.UUID) -> MobitelEmployee:
    employee = get_employee(db, employee_id)
    employee.is_deleted = True
    db.commit()
    db.refresh(employee)
    return employee


def set_status(db: Session, employee_id: uuid.UUID, status: MobitelEmployeeStatus) -> MobitelEmployee:
    employee = get_employee(db, employee_id)
    employee.status = status
    db.commit()
    db.refresh(employee)
    return employee