import uuid

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.dialog_mobile_employee import DialogMobileEmployee
from app.models.dialog_mobile_employee_audit_log import DialogMobileEmployeeAuditLog
from app.models.dialog_mobile_mobile_number import DialogMobileMobileNumber, DialogMobileMobileNumberStatus
from app.schemas.dialog_mobile_employee import DialogMobileEmployeeCreate, DialogMobileEmployeeUpdate
from app.schemas.dialog_mobile_mobile_number import DialogMobileMobileNumberCreate


def _log(db: Session, employee_id: uuid.UUID, change_type: str, old_values: dict | None, new_values: dict | None):
    db.add(DialogMobileEmployeeAuditLog(
        employee_id=employee_id,
        change_type=change_type,
        old_values=old_values,
        new_values=new_values,
    ))


def _assert_number_available(db: Session, mobile_no: str):
    clash = db.query(DialogMobileMobileNumber).filter(
        DialogMobileMobileNumber.mobile_no == mobile_no,
        DialogMobileMobileNumber.status == DialogMobileMobileNumberStatus.active,
    ).first()
    if clash:
        owner = db.query(DialogMobileEmployee).filter(DialogMobileEmployee.id == clash.employee_id).first()
        owner_name = owner.name if owner else "another employee"
        raise HTTPException(status_code=409, detail=f"Mobile number {mobile_no} is already active for {owner_name}")


def list_employees(
    db: Session,
    search: str | None = None,
    lob: str | None = None,
    include_deleted: bool = False,
) -> list[DialogMobileEmployee]:
    query = db.query(DialogMobileEmployee)

    if not include_deleted:
        query = query.filter(DialogMobileEmployee.is_deleted.is_(False))

    if lob:
        query = query.filter(DialogMobileEmployee.lob == lob)

    if search:
        pattern = f"%{search}%"
        matching_employee_ids = db.query(DialogMobileMobileNumber.employee_id).filter(
            DialogMobileMobileNumber.mobile_no.ilike(pattern)
        )
        query = query.filter(or_(
            DialogMobileEmployee.name.ilike(pattern),
            DialogMobileEmployee.emp_no.ilike(pattern),
            DialogMobileEmployee.id.in_(matching_employee_ids),
        ))

    return query.order_by(DialogMobileEmployee.name).all()


def get_employee(db: Session, employee_id: uuid.UUID) -> DialogMobileEmployee:
    employee = db.query(DialogMobileEmployee).filter(DialogMobileEmployee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


def create_employee(db: Session, payload: DialogMobileEmployeeCreate) -> DialogMobileEmployee:
    existing = db.query(DialogMobileEmployee).filter(
        DialogMobileEmployee.emp_no == payload.emp_no,
        DialogMobileEmployee.is_deleted.is_(False),
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"EMP No {payload.emp_no} already exists")

    if payload.mobile_no:
        _assert_number_available(db, payload.mobile_no)

    employee_fields = payload.model_dump(exclude={"mobile_no"})
    employee = DialogMobileEmployee(**employee_fields)
    db.add(employee)
    db.flush()

    if payload.mobile_no:
        db.add(DialogMobileMobileNumber(employee_id=employee.id, mobile_no=payload.mobile_no, is_primary=True))

    _log(db, employee.id, "created", None, payload.model_dump(mode="json"))
    db.commit()
    db.refresh(employee)
    return employee


def update_employee(db: Session, employee_id: uuid.UUID, payload: DialogMobileEmployeeUpdate) -> DialogMobileEmployee:
    employee = get_employee(db, employee_id)
    old_values = {c.name: str(getattr(employee, c.name)) for c in employee.__table__.columns}

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(employee, field, value)

    _log(db, employee.id, "updated", old_values, {k: str(v) for k, v in updates.items()})
    db.commit()
    db.refresh(employee)
    return employee


def soft_delete_employee(db: Session, employee_id: uuid.UUID) -> DialogMobileEmployee:
    employee = get_employee(db, employee_id)
    employee.is_deleted = True

    _log(db, employee.id, "deleted", None, None)
    db.commit()
    db.refresh(employee)
    return employee


def add_mobile_number(db: Session, employee_id: uuid.UUID, payload: DialogMobileMobileNumberCreate) -> DialogMobileMobileNumber:
    employee = get_employee(db, employee_id)
    _assert_number_available(db, payload.mobile_no)

    if payload.is_primary:
        db.query(DialogMobileMobileNumber).filter(DialogMobileMobileNumber.employee_id == employee.id).update({"is_primary": False})

    number = DialogMobileMobileNumber(
        employee_id=employee.id, mobile_no=payload.mobile_no, is_primary=payload.is_primary,
        project_label=payload.project_label,
    )
    db.add(number)
    _log(db, employee.id, "mobile_number_added", None, {"mobile_no": payload.mobile_no})
    db.commit()
    db.refresh(number)
    return number


def update_mobile_number_project_label(db: Session, number_id: uuid.UUID, project_label: str | None) -> DialogMobileMobileNumber:
    number = db.query(DialogMobileMobileNumber).filter(DialogMobileMobileNumber.id == number_id).first()
    if not number:
        raise HTTPException(status_code=404, detail="Mobile number not found")
    number.project_label = project_label
    db.commit()
    db.refresh(number)
    return number


def remove_mobile_number(db: Session, employee_id: uuid.UUID, number_id: uuid.UUID) -> DialogMobileMobileNumber:
    number = db.query(DialogMobileMobileNumber).filter(
        DialogMobileMobileNumber.id == number_id,
        DialogMobileMobileNumber.employee_id == employee_id,
    ).first()
    if not number:
        raise HTTPException(status_code=404, detail="Mobile number not found for this employee")

    number.status = DialogMobileMobileNumberStatus.inactive
    _log(db, employee_id, "mobile_number_removed", None, {"mobile_no": number.mobile_no})
    db.commit()
    db.refresh(number)
    return number