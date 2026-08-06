import uuid

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.dialog_data_employee import DialogDataEmployee
from app.models.dialog_data_connection import DialogDataConnection, DialogDataConnectionStatus
from app.schemas.dialog_data_employee import DialogDataEmployeeCreate, DialogDataEmployeeUpdate, DialogDataConnectionCreate


def list_employees(db: Session, search: str | None = None, include_deleted: bool = False) -> list[DialogDataEmployee]:
    query = db.query(DialogDataEmployee)

    if not include_deleted:
        query = query.filter(DialogDataEmployee.is_deleted.is_(False))

    if search:
        pattern = f"%{search}%"
        query = query.filter(or_(
            DialogDataEmployee.name.ilike(pattern),
            DialogDataEmployee.emp_no.ilike(pattern),
        ))

    return query.order_by(DialogDataEmployee.name).all()


def get_employee(db: Session, employee_id: uuid.UUID) -> DialogDataEmployee:
    employee = db.query(DialogDataEmployee).filter(DialogDataEmployee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Dialog Data Bucket employee not found")
    return employee


def create_employee(db: Session, payload: DialogDataEmployeeCreate) -> DialogDataEmployee:
    existing_emp_no = db.query(DialogDataEmployee).filter(
        DialogDataEmployee.emp_no == payload.emp_no, DialogDataEmployee.is_deleted.is_(False)
    ).first()
    if existing_emp_no:
        raise HTTPException(status_code=409, detail=f"EMP No {payload.emp_no} already exists")

    employee = DialogDataEmployee(emp_no=payload.emp_no, name=payload.name, team=payload.team)
    db.add(employee)
    db.flush()

    if payload.connection_no:
        add_connection(db, employee.id, DialogDataConnectionCreate(connection_no=payload.connection_no), _commit=False)

    db.commit()
    db.refresh(employee)
    return employee


def update_employee(db: Session, employee_id: uuid.UUID, payload: DialogDataEmployeeUpdate) -> DialogDataEmployee:
    employee = get_employee(db, employee_id)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(employee, field, value)
    db.commit()
    db.refresh(employee)
    return employee


def soft_delete_employee(db: Session, employee_id: uuid.UUID) -> DialogDataEmployee:
    employee = get_employee(db, employee_id)
    employee.is_deleted = True
    db.commit()
    db.refresh(employee)
    return employee


def add_connection(db: Session, employee_id: uuid.UUID, payload: DialogDataConnectionCreate, _commit: bool = True) -> DialogDataEmployee:
    employee = get_employee(db, employee_id)

    existing = db.query(DialogDataConnection).filter(
        DialogDataConnection.connection_no == payload.connection_no, DialogDataConnection.is_deleted.is_(False)
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Connection {payload.connection_no} is already in use")

    db.add(DialogDataConnection(employee_id=employee.id, connection_no=payload.connection_no))
    if _commit:
        db.commit()
        db.refresh(employee)
    return employee


def remove_connection(db: Session, connection_id: uuid.UUID) -> None:
    connection = db.query(DialogDataConnection).filter(DialogDataConnection.id == connection_id).first()
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    connection.is_deleted = True
    db.commit()