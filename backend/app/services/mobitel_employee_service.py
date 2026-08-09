import uuid

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.mobitel_employee import MobitelEmployee
from app.models.mobitel_connection import MobitelConnection, MobitelConnectionStatus
from app.schemas.mobitel_employee import MobitelEmployeeCreate, MobitelEmployeeUpdate, MobitelConnectionCreate


def list_employees(db: Session, search: str | None = None, include_pool: bool = True) -> list[MobitelEmployee]:
    query = db.query(MobitelEmployee).filter(MobitelEmployee.is_deleted.is_(False))
    if not include_pool:
        query = query.filter(MobitelEmployee.is_pool.is_(False))
    if search:
        pattern = f"%{search}%"
        query = query.filter(or_(MobitelEmployee.name.ilike(pattern), MobitelEmployee.emp_no.ilike(pattern)))
    return query.order_by(MobitelEmployee.name).all()


def get_employee(db: Session, employee_id: uuid.UUID) -> MobitelEmployee:
    employee = db.query(MobitelEmployee).filter(MobitelEmployee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Mobitel employee not found")
    return employee


def create_employee(db: Session, payload: MobitelEmployeeCreate) -> MobitelEmployee:
    existing = db.query(MobitelEmployee).filter(
        MobitelEmployee.emp_no == payload.emp_no, MobitelEmployee.is_deleted.is_(False)
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"EMP No {payload.emp_no} already exists")

    employee = MobitelEmployee(emp_no=payload.emp_no, name=payload.name, lob=payload.lob, lob_code=payload.lob_code)
    db.add(employee)
    db.flush()

    if payload.mobile_no:
        add_connection(db, employee.id, MobitelConnectionCreate(mobile_no=payload.mobile_no), _commit=False)

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


def add_connection(db: Session, employee_id: uuid.UUID, payload: MobitelConnectionCreate, _commit: bool = True) -> MobitelEmployee:
    employee = get_employee(db, employee_id)

    existing = db.query(MobitelConnection).filter(
        MobitelConnection.mobile_no == payload.mobile_no, MobitelConnection.is_deleted.is_(False)
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Mobile number {payload.mobile_no} is already in use")

    db.add(MobitelConnection(employee_id=employee.id, mobile_no=payload.mobile_no))
    if _commit:
        db.commit()
        db.refresh(employee)
    return employee


def remove_connection(db: Session, connection_id: uuid.UUID) -> None:
    connection = db.query(MobitelConnection).filter(MobitelConnection.id == connection_id).first()
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    connection.is_deleted = True
    db.commit()