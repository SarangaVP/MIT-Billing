import uuid
from datetime import date, datetime
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.ingestion.pdf_summary_parser import parse_summary_table, extract_cover_page_totals
from app.models.bill_period import BillPeriod
from app.models.bill_line_item import BillLineItem
from app.models.bucket_rate import BucketRate
from app.models.mobile_number import MobileNumber
from app.models.employee import Employee
from app.schemas.bill import BillSummaryRow, ImportResult, ApprovalOverrideInput


def _parse_ddmmyyyy(value: str | None) -> date | None:
    if not value:
        return None
    return datetime.strptime(value, "%m/%d/%Y").date()


def import_bill_pdf(db: Session, pdf_path: str, label: str) -> ImportResult:
    rows = parse_summary_table(pdf_path)
    if not rows:
        raise HTTPException(status_code=422, detail="No summary rows found in this PDF — check the file format")

    cover = extract_cover_page_totals(pdf_path)
    parsed_total = sum(Decimal(str(r["charges_for_bill_period"])) for r in rows)
    stated_total = Decimal(str(cover["stated_total_charges_for_bill_period"])) if cover["stated_total_charges_for_bill_period"] is not None else None

    reconciled = stated_total is not None and abs(parsed_total - stated_total) < Decimal("0.01")
    if stated_total is not None and not reconciled:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Reconciliation failed: parsed line items sum to {parsed_total}, "
                f"but the invoice states {stated_total}. Import aborted — nothing was saved."
            ),
        )

    bill_period = BillPeriod(
        label=label,
        corporate_code=cover["corporate_code"],
        bill_period_start=_parse_ddmmyyyy(cover["bill_period_start"]),
        bill_period_end=_parse_ddmmyyyy(cover["bill_period_end"]),
        invoice_date=_parse_ddmmyyyy(cover["invoice_date"]),
        stated_total_charges_for_bill_period=stated_total,
        stated_total_due_amount=Decimal(str(cover["stated_total_due_amount"])) if cover["stated_total_due_amount"] is not None else None,
    )
    db.add(bill_period)
    db.flush()

    for row in rows:
        db.add(BillLineItem(
            bill_period_id=bill_period.id,
            mobile_no=row["mobile_no"],
            previous_due_amount=row["previous_due_amount"],
            payments=row["payments"],
            total_usage_charges=row["total_usage_charges"],
            idd=row["idd"],
            roaming=row["roaming"],
            vas=row["vas"],
            discounts=row["discounts"],
            bill_adjustments_balance_transfers=row["bill_adjustments_balance_transfers"],
            commitment_charges=row["commitment_charges"],
            late_payment_charges=row["late_payment_charges"],
            add_to_bill_charges=row["add_to_bill_charges"],
            instalment_plans=row["instalment_plans"],
            govt_taxes=row["govt_taxes"],
            vat=row["vat"],
            charges_for_bill_period=row["charges_for_bill_period"],
            total_due_amount=row["total_due_amount"],
        ))

    db.commit()
    db.refresh(bill_period)

    return ImportResult(
        bill_period_id=bill_period.id,
        line_items_imported=len(rows),
        parsed_total_charges_for_bill_period=parsed_total,
        stated_total_charges_for_bill_period=stated_total,
        reconciled=reconciled,
    )


def _get_active_bucket_rate(db: Session, as_of: date) -> BucketRate | None:
    return (
        db.query(BucketRate)
        .filter(BucketRate.effective_from <= as_of)
        .order_by(BucketRate.effective_from.desc())
        .first()
    )


def get_bill_period(db: Session, bill_period_id: uuid.UUID) -> BillPeriod:
    period = db.query(BillPeriod).filter(BillPeriod.id == bill_period_id).first()
    if not period:
        raise HTTPException(status_code=404, detail="Bill period not found")
    return period


def list_bill_periods(db: Session) -> list[BillPeriod]:
    return db.query(BillPeriod).order_by(BillPeriod.bill_period_start.desc().nullslast()).all()


def get_summary(db: Session, bill_period_id: uuid.UUID) -> list[BillSummaryRow]:
    period = get_bill_period(db, bill_period_id)
    line_items = db.query(BillLineItem).filter(BillLineItem.bill_period_id == period.id).all()
    return _build_summary_rows(db, line_items, as_of=period.invoice_date)


def get_summary_row_for_line_item(db: Session, line_item_id: uuid.UUID) -> BillSummaryRow:
    line_item = db.query(BillLineItem).filter(BillLineItem.id == line_item_id).first()
    if not line_item:
        raise HTTPException(status_code=404, detail="Bill line item not found")
    period = get_bill_period(db, line_item.bill_period_id)
    rows = _build_summary_rows(db, [line_item], as_of=period.invoice_date)
    return rows[0]


def _build_summary_rows(db: Session, line_items: list[BillLineItem], as_of: date | None) -> list[BillSummaryRow]:
    as_of = as_of or datetime.utcnow().date()
    bucket_rate = _get_active_bucket_rate(db, as_of)
    bucket_cost = bucket_rate.cost if bucket_rate else Decimal("0")
    bucket_vat = bucket_rate.vat if bucket_rate else Decimal("0")
    bucket_nett = bucket_cost - bucket_vat

    mobile_nos = [li.mobile_no for li in line_items]
    number_rows = (
        db.query(MobileNumber, Employee)
        .join(Employee, Employee.id == MobileNumber.employee_id)
        .filter(MobileNumber.mobile_no.in_(mobile_nos))
        .all()
    )
    employee_by_mobile = {mn.mobile_no: emp for mn, emp in number_rows}

    results = []
    for li in line_items:
        employee = employee_by_mobile.get(li.mobile_no)

        net_amount = li.charges_for_bill_period - li.vat
        total = net_amount + bucket_nett
        salary_deduction = li.vas

        if li.approval_override:
            need_approval = li.approval_override
            is_overridden = True
        else:
            credit_limit = employee.credit_limit if employee and employee.credit_limit is not None else Decimal("0")
            need_approval = "OK" if net_amount <= credit_limit else "Need Approval"
            is_overridden = False

        results.append(BillSummaryRow(
            bill_line_item_id=li.id,
            mobile_no=li.mobile_no,
            emp_no=employee.emp_no if employee else None,
            name=employee.name if employee else None,
            lob=employee.lob if employee else None,
            cadre=employee.cadre if employee else None,
            credit_limit=employee.credit_limit if employee else None,
            level=employee.level if employee else None,
            email=employee.email if employee else None,
            total_usage_charges=li.total_usage_charges,
            idd=li.idd,
            roaming=li.roaming,
            vas=li.vas,
            charges_for_bill_period=li.charges_for_bill_period,
            vat=li.vat,
            add_to_bill_charges=li.add_to_bill_charges,
            net_amount=net_amount,
            bucket_cost=bucket_cost,
            bucket_vat=bucket_vat,
            bucket_nett=bucket_nett,
            total=total,
            salary_deduction=salary_deduction,
            need_approval=need_approval,
            is_overridden=is_overridden,
        ))

    return results


def set_approval_override(db: Session, line_item_id: uuid.UUID, payload: ApprovalOverrideInput) -> BillSummaryRow:
    line_item = db.query(BillLineItem).filter(BillLineItem.id == line_item_id).first()
    if not line_item:
        raise HTTPException(status_code=404, detail="Bill line item not found")

    line_item.approval_override = payload.approval_override
    db.commit()
    db.refresh(line_item)
    return get_summary_row_for_line_item(db, line_item_id)