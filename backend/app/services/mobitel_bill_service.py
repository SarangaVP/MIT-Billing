import uuid
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.ingestion.mobitel_pdf_parser import parse_mobitel_bill
from app.models.mobitel_bill_period import MobitelBillPeriod
from app.models.mobitel_bill_line_item import MobitelBillLineItem
from app.models.mobitel_employee import MobitelEmployee, MobitelEmployeeStatus
from app.schemas.mobitel_bill import MobitelImportResult
from app.services.mobitel_static_ip_service import get_active_static_ip_costs


def _resolve_period_dates(bill_date, start_dm, end_dm):
    if not start_dm or not end_dm:
        return None, None
    end_day, end_month = (int(x) for x in end_dm.split("/"))
    start_day, start_month = (int(x) for x in start_dm.split("/"))
    end_year = bill_date.year
    start_year = bill_date.year if start_month <= end_month else bill_date.year - 1
    return date(start_year, start_month, start_day), date(end_year, end_month, end_day)


def import_mobitel_bill(db: Session, pdf_path: str, label: str) -> MobitelImportResult:
    parsed = parse_mobitel_bill(pdf_path)

    if parsed["bucket"] is None or parsed["vat"] is None:
        raise HTTPException(
            status_code=422,
            detail="Could not find 'Total Charge for the Month' or 'VAT' in this PDF — check the file format",
        )

    bucket = Decimal(str(parsed["bucket"]))
    vat = Decimal(str(parsed["vat"]))
    net = bucket - vat

    bill_date = datetime.strptime(parsed["bill_date"], "%d/%m/%Y").date() if parsed["bill_date"] else None
    due_date = datetime.strptime(parsed["due_date"], "%d/%m/%Y").date() if parsed["due_date"] else None
    period_start, period_end = (
        _resolve_period_dates(bill_date, parsed["period_start_dm"], parsed["period_end_dm"])
        if bill_date else (None, None)
    )
    as_of = bill_date or datetime.utcnow().date()

    active_employees = (
        db.query(MobitelEmployee)
        .filter(MobitelEmployee.status == MobitelEmployeeStatus.active, MobitelEmployee.is_deleted.is_(False))
        .all()
    )
    users = len(active_employees)
    if users == 0:
        raise HTTPException(status_code=422, detail="No active Mobitel employees to split this bill across")

    static_ip_costs = get_active_static_ip_costs(db, as_of)
    total_static_ip = sum(static_ip_costs.values()) if static_ip_costs else Decimal("0")

    per_user_cost = ((net - total_static_ip) / users).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

    bill_period = MobitelBillPeriod(
        label=label, bill_no=parsed["bill_no"], account_no=parsed["account_no"],
        bill_date=bill_date, due_date=due_date, period_start=period_start, period_end=period_end,
        arrears=Decimal(str(parsed["arrears"])) if parsed["arrears"] is not None else None,
        bucket_total=bucket, vat=vat, net=net,
        total_payable=Decimal(str(parsed["total_payable"])) if parsed["total_payable"] is not None else None,
        users_count=users, per_user_cost=per_user_cost,
    )
    db.add(bill_period)
    db.flush()

    line_total = Decimal("0")
    for employee in active_employees:
        static_ip_cost = static_ip_costs.get(employee.id, Decimal("0"))
        total = (per_user_cost + static_ip_cost).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        line_total += total

        db.add(MobitelBillLineItem(
            bill_period_id=bill_period.id, employee_id=employee.id,
            data_cost=per_user_cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            static_ip_cost=static_ip_cost, total=total,
        ))

    discrepancy = line_total - net
    reconciled = abs(discrepancy) < Decimal("0.01")

    bill_period.reconciled = reconciled
    bill_period.reconciliation_discrepancy = discrepancy

    db.commit()
    db.refresh(bill_period)

    return MobitelImportResult(
        bill_period_id=bill_period.id, line_items_created=users, users_count=users,
        net=net, per_user_cost=per_user_cost, parsed_total=line_total,
        reconciled=reconciled, reconciliation_discrepancy=discrepancy,
    )


def list_bill_periods(db: Session) -> list[MobitelBillPeriod]:
    return db.query(MobitelBillPeriod).order_by(MobitelBillPeriod.bill_date.desc().nullslast()).all()


def get_bill_period(db: Session, bill_period_id: uuid.UUID) -> MobitelBillPeriod:
    period = db.query(MobitelBillPeriod).filter(MobitelBillPeriod.id == bill_period_id).first()
    if not period:
        raise HTTPException(status_code=404, detail="Mobitel bill period not found")
    return period


def get_summary(db: Session, bill_period_id: uuid.UUID) -> list[dict]:
    get_bill_period(db, bill_period_id)
    rows = (
        db.query(MobitelBillLineItem, MobitelEmployee)
        .join(MobitelEmployee, MobitelEmployee.id == MobitelBillLineItem.employee_id)
        .filter(MobitelBillLineItem.bill_period_id == bill_period_id)
        .order_by(MobitelEmployee.name)
        .all()
    )
    return [
        {
            "id": li.id, "employee_id": li.employee_id, "emp_no": emp.emp_no, "name": emp.name,
            "lob": emp.lob, "mobile_no": emp.mobile_no, "data_cost": li.data_cost,
            "static_ip_cost": li.static_ip_cost, "total": li.total,
        }
        for li, emp in rows
    ]