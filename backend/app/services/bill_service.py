import uuid
from datetime import date, datetime
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.ingestion.pdf_summary_parser import (
    parse_summary_table as parse_pdf_summary_table,
    extract_cover_page_totals as extract_pdf_cover_totals,
)
from app.ingestion.xls_summary_parser import (
    parse_summary_table as parse_xls_summary_table,
    extract_cover_page_totals as extract_xls_cover_totals,
)
from app.models.bill_period import BillPeriod
from app.models.bill_line_item import BillLineItem
from app.models.bucket_rate import BucketRate
from app.models.mobile_number import MobileNumber
from app.models.employee import Employee
from app.schemas.bill import BillSummaryRow, ImportResult, ApprovalOverrideInput


def _parse_date(value: str | None, fmt: str) -> date | None:
    if not value:
        return None
    return datetime.strptime(value, fmt).date()


def import_bill_file(db: Session, file_path: str, label: str, source_format: str) -> ImportResult:
    """
    source_format: "pdf" or "xls". Both produce the same downstream shape —
    everything after parsing is format-agnostic.
    """
    if source_format == "pdf":
        rows = parse_pdf_summary_table(file_path)
        cover = extract_pdf_cover_totals(file_path)
        date_fmt = "%m/%d/%Y"   # PDF explicitly labels its dates MM/DD/YYYY
    elif source_format == "xls":
        rows = parse_xls_summary_table(file_path)
        cover = extract_xls_cover_totals(file_path)
        date_fmt = "%d/%m/%Y"   # confirmed against a real bill — opposite of the PDF
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {source_format}")

    if not rows:
        raise HTTPException(status_code=422, detail="No summary rows found in this file — check the format")

    stated_total = (
        Decimal(str(cover["stated_total_charges_for_bill_period"]))
        if cover.get("stated_total_charges_for_bill_period") is not None
        else None
    )
    parsed_total = sum(Decimal(str(r["charges_for_bill_period"])) for r in rows)
    discrepancy = (parsed_total - stated_total) if stated_total is not None else None

    if source_format == "pdf":
        # Strict: this source has always reconciled exactly in testing. A
        # mismatch here means something is genuinely wrong — reject outright.
        reconciled = stated_total is not None and abs(discrepancy) < Decimal("0.01")
        if stated_total is not None and not reconciled:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Reconciliation failed: parsed line items sum to {parsed_total}, "
                    f"but the invoice states {stated_total}. Import aborted — nothing was saved."
                ),
            )
    else:
        # Relaxed: this source structurally omits some dormant/zero-activity
        # accounts, so a mismatch is expected. Never block the import on
        # this — always save the data and report the exact discrepancy, so
        # a human can review it rather than being locked out of the import.
        reconciled = stated_total is not None and abs(discrepancy) < Decimal("0.01")

    bill_period = BillPeriod(
        label=label,
        corporate_code=cover.get("corporate_code"),
        bill_period_start=_parse_date(cover.get("bill_period_start"), date_fmt),
        bill_period_end=_parse_date(cover.get("bill_period_end"), date_fmt),
        invoice_date=_parse_date(cover.get("invoice_date"), date_fmt),
        stated_total_charges_for_bill_period=stated_total,
        stated_total_due_amount=(
            Decimal(str(cover["stated_total_due_amount"]))
            if cover.get("stated_total_due_amount") is not None
            else None
        ),
        source_format=source_format,
        reconciled=reconciled,
        reconciliation_discrepancy=discrepancy,
    )
    db.add(bill_period)
    db.flush()

    for row in rows:
        db.add(BillLineItem(
            bill_period_id=bill_period.id,
            mobile_no=row["mobile_no"],
            previous_due_amount=row.get("previous_due_amount", 0),
            payments=row.get("payments", 0),
            total_usage_charges=row.get("total_usage_charges", 0),
            idd=row.get("idd", 0),
            roaming=row.get("roaming", 0),
            vas=row.get("vas", 0),
            discounts=row.get("discounts", 0),
            bill_adjustments_balance_transfers=row.get("bill_adjustments_balance_transfers", 0),
            commitment_charges=row.get("commitment_charges", 0),
            late_payment_charges=row.get("late_payment_charges", 0),
            add_to_bill_charges=row.get("add_to_bill_charges", 0),
            instalment_plans=row.get("instalment_plans", 0),
            govt_taxes=row.get("govt_taxes", 0),
            vat=row.get("vat", 0),
            charges_for_bill_period=row.get("charges_for_bill_period", 0),
            total_due_amount=row.get("total_due_amount", 0),
            # Only present when source_format == "xls" — None for PDF rows
            voice_rental=row.get("voice_rental"),
            voice_usage=row.get("voice_usage"),
            sms=row.get("sms"),
            data_rental=row.get("data_rental"),
            data_usage=row.get("data_usage"),
        ))

    db.commit()
    db.refresh(bill_period)

    return ImportResult(
        bill_period_id=bill_period.id,
        line_items_imported=len(rows),
        parsed_total_charges_for_bill_period=parsed_total,
        stated_total_charges_for_bill_period=stated_total,
        reconciled=reconciled,
        reconciliation_discrepancy=discrepancy,
        source_format=source_format,
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


def delete_bill_period(db: Session, bill_period_id: uuid.UUID) -> None:
    period = get_bill_period(db, bill_period_id)  # 404 if missing
    db.query(BillLineItem).filter(BillLineItem.bill_period_id == period.id).delete()
    db.delete(period)
    db.commit()


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
    standard_bucket_cost = bucket_rate.cost if bucket_rate else Decimal("0")
    standard_bucket_vat = bucket_rate.vat if bucket_rate else Decimal("0")

    mobile_nos = [li.mobile_no for li in line_items]
    number_rows = (
        db.query(MobileNumber, Employee)
        .join(Employee, Employee.id == MobileNumber.employee_id)
        .filter(MobileNumber.mobile_no.in_(mobile_nos))
        .all()
    )
    employee_by_mobile = {mn.mobile_no: emp for mn, emp in number_rows}
    # project_label lives on MobileNumber, not Employee — the dict above
    # only kept the Employee half of the join, so this was previously
    # discarded entirely and had no way to reach the summary row.
    project_label_by_mobile = {mn.mobile_no: mn.project_label for mn, emp in number_rows}

    results = []
    for li in line_items:
        employee = employee_by_mobile.get(li.mobile_no)

        # Confirmed against real data: a number that's disconnected that
        # month shows EXACTLY zero total_usage_charges AND zero
        # charges_for_bill_period on the actual telecom invoice — checked
        # against 611 genuinely active numbers (0 false positives) and
        # 139 genuinely disconnected numbers (139/139 correctly zero) in
        # a real July bill. The bucket allocation shouldn't apply to a
        # disconnected number — this is a real signal already present in
        # the bill itself, not something requiring any external status
        # tracking.
        is_disconnected_this_month = li.total_usage_charges == 0 and li.charges_for_bill_period == 0

        # Confirmed against a SEPARATE real bill: Interns never get the
        # bucket allocation, even with substantial real usage that
        # month — 100% clean across 82 real Intern rows, zero exceptions
        # either direction. Unlike disconnection, this genuinely can't be
        # inferred from usage — it's tied to cadre, which we already
        # store on the employee. Also confirmed the handful of remaining
        # exceptions in that same file are exactly our already-modeled
        # "General" lines (is_general_line) — those aren't real personal
        # employees, so excluding them here too is consistent.
        is_intern = bool(employee and employee.cadre and employee.cadre.strip().lower() == "intern")
        is_general_line = bool(employee and employee.is_general_line)

        if is_disconnected_this_month or is_intern or is_general_line:
            bucket_cost = Decimal("0")
            bucket_vat = Decimal("0")
        else:
            bucket_cost = standard_bucket_cost
            bucket_vat = standard_bucket_vat
        bucket_nett = bucket_cost - bucket_vat

        net_amount = li.charges_for_bill_period - li.vat
        total = net_amount + bucket_nett
        # Salary Deduction = VAS + Add To Bill Charges (both are personal/
        # extra charges recovered via payroll, per current business rule —
        # note this differs from the one Excel snapshot we originally
        # reverse-engineered, which only used VAS; this is the corrected rule).
        salary_deduction = li.vas + li.add_to_bill_charges

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
            project_label=project_label_by_mobile.get(li.mobile_no),
            total_usage_charges=li.total_usage_charges,
            voice_rental=li.voice_rental,
            voice_usage=li.voice_usage,
            sms=li.sms,
            data_rental=li.data_rental,
            data_usage=li.data_usage,
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