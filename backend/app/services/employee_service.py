import uuid

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.employee import Employee, EmployeeStatus
from app.models.employee_audit_log import EmployeeAuditLog
from app.models.employee_transition import EmployeeTransition, TransitionType
from app.models.mobile_number import MobileNumber, MobileNumberStatus
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, ResignRequest, TransferRequest
from app.schemas.mobile_number import MobileNumberCreate


def _log(db: Session, employee_id: uuid.UUID, change_type: str, old_values: dict | None, new_values: dict | None):
    db.add(EmployeeAuditLog(
        employee_id=employee_id,
        change_type=change_type,
        old_values=old_values,
        new_values=new_values,
    ))


def _assert_number_available(db: Session, mobile_no: str):
    clash = db.query(MobileNumber).filter(
        MobileNumber.mobile_no == mobile_no,
        MobileNumber.status == MobileNumberStatus.active,
    ).first()
    if clash:
        owner = db.query(Employee).filter(Employee.id == clash.employee_id).first()
        owner_name = owner.name if owner else "another employee"
        raise HTTPException(status_code=409, detail=f"Mobile number {mobile_no} is already active for {owner_name}")


def list_employees(
    db: Session,
    search: str | None = None,
    lob: str | None = None,
    status: EmployeeStatus | None = None,
    include_deleted: bool = False,
) -> list[Employee]:
    query = db.query(Employee)

    if not include_deleted:
        query = query.filter(Employee.is_deleted.is_(False))

    if status:
        query = query.filter(Employee.status == status)

    if lob:
        query = query.filter(Employee.lob == lob)

    if search:
        pattern = f"%{search}%"
        matching_employee_ids = db.query(MobileNumber.employee_id).filter(
            MobileNumber.mobile_no.ilike(pattern)
        )
        query = query.filter(or_(
            Employee.name.ilike(pattern),
            Employee.emp_no.ilike(pattern),
            Employee.id.in_(matching_employee_ids),
        ))

    return query.order_by(Employee.name).all()


def get_employee(db: Session, employee_id: uuid.UUID) -> Employee:
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


def create_employee(db: Session, payload: EmployeeCreate) -> Employee:
    existing = db.query(Employee).filter(
        Employee.emp_no == payload.emp_no,
        Employee.is_deleted.is_(False),
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"EMP No {payload.emp_no} already exists")

    if payload.mobile_no:
        _assert_number_available(db, payload.mobile_no)

    employee_fields = payload.model_dump(exclude={"mobile_no"})
    employee = Employee(**employee_fields)
    db.add(employee)
    db.flush()

    if payload.mobile_no:
        db.add(MobileNumber(employee_id=employee.id, mobile_no=payload.mobile_no, is_primary=True))

    _log(db, employee.id, "created", None, payload.model_dump(mode="json"))
    db.commit()
    db.refresh(employee)
    return employee


def update_employee(db: Session, employee_id: uuid.UUID, payload: EmployeeUpdate) -> Employee:
    employee = get_employee(db, employee_id)
    old_values = {c.name: str(getattr(employee, c.name)) for c in employee.__table__.columns}

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(employee, field, value)

    _log(db, employee.id, "updated", old_values, {k: str(v) for k, v in updates.items()})
    db.commit()
    db.refresh(employee)
    return employee


def soft_delete_employee(db: Session, employee_id: uuid.UUID) -> Employee:
    employee = get_employee(db, employee_id)
    employee.is_deleted = True

    _log(db, employee.id, "deleted", None, None)
    db.commit()
    db.refresh(employee)
    return employee


def resign_employee(db: Session, employee_id: uuid.UUID, payload: ResignRequest) -> Employee:
    employee = get_employee(db, employee_id)
    employee.status = EmployeeStatus.resigned

    numbers = db.query(MobileNumber).filter(
        MobileNumber.employee_id == employee.id,
        MobileNumber.status == MobileNumberStatus.active,
    ).all()

    for number in numbers:
        db.add(EmployeeTransition(
            employee_id=employee.id,
            type=TransitionType.resigned,
            old_mobile_no=number.mobile_no,
            effective_date=payload.effective_date,
            notes=payload.notes,
        ))

    _log(db, employee.id, "resigned", None, {"effective_date": str(payload.effective_date)})
    db.commit()
    db.refresh(employee)
    return employee


def transfer_employee_number(db: Session, employee_id: uuid.UUID, payload: TransferRequest) -> Employee:
    from_employee = get_employee(db, employee_id)
    to_employee = get_employee(db, payload.new_employee_id)

    number = db.query(MobileNumber).filter(
        MobileNumber.employee_id == from_employee.id,
        MobileNumber.mobile_no == payload.mobile_no,
        MobileNumber.status == MobileNumberStatus.active,
    ).first()
    if not number:
        raise HTTPException(
            status_code=404,
            detail=f"{from_employee.name} has no active number {payload.mobile_no}",
        )

    number.employee_id = to_employee.id
    number.is_primary = False

    remaining_active = db.query(MobileNumber).filter(
        MobileNumber.employee_id == from_employee.id,
        MobileNumber.status == MobileNumberStatus.active,
    ).count()
    if remaining_active == 0:
        from_employee.status = EmployeeStatus.transferred

    db.add(EmployeeTransition(
        employee_id=from_employee.id,
        type=TransitionType.transferred,
        old_mobile_no=payload.mobile_no,
        new_employee_id=to_employee.id,
        effective_date=payload.effective_date,
        notes=payload.notes,
    ))
    _log(db, from_employee.id, "transferred", None, {
        "mobile_no": payload.mobile_no,
        "new_employee_id": str(to_employee.id),
    })
    db.commit()
    db.refresh(from_employee)
    return from_employee


def add_mobile_number(db: Session, employee_id: uuid.UUID, payload: MobileNumberCreate) -> MobileNumber:
    employee = get_employee(db, employee_id)
    _assert_number_available(db, payload.mobile_no)

    if payload.is_primary:
        db.query(MobileNumber).filter(MobileNumber.employee_id == employee.id).update({"is_primary": False})

    number = MobileNumber(employee_id=employee.id, mobile_no=payload.mobile_no, is_primary=payload.is_primary)
    db.add(number)
    _log(db, employee.id, "mobile_number_added", None, {"mobile_no": payload.mobile_no})
    db.commit()
    db.refresh(number)
    return number


def remove_mobile_number(db: Session, employee_id: uuid.UUID, number_id: uuid.UUID) -> MobileNumber:
    number = db.query(MobileNumber).filter(
        MobileNumber.id == number_id,
        MobileNumber.employee_id == employee_id,
    ).first()
    if not number:
        raise HTTPException(status_code=404, detail="Mobile number not found for this employee")

    number.status = MobileNumberStatus.inactive
    _log(db, employee_id, "mobile_number_removed", None, {"mobile_no": number.mobile_no})
    db.commit()
    db.refresh(number)
    return number