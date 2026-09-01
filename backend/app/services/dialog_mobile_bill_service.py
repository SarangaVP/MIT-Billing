import uuid
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP

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
from app.models.dialog_mobile_bill_period import DialogMobileBillPeriod
from app.models.dialog_mobile_bill_line_item import DialogMobileBillLineItem
from app.models.dialog_mobile_mobile_number import DialogMobileMobileNumber
from app.models.dialog_mobile_employee import DialogMobileEmployee
from app.schemas.dialog_mobile_bill import (
    DialogMobileBillSummaryRow, DialogMobileImportResult, DialogMobileApprovalOverrideInput,
    DialogMobileLineItemChargeUpdateInput,
)


def _is_disconnected_this_month(li: DialogMobileBillLineItem) -> bool:
    return li.total_usage_charges == 0 and li.charges_for_bill_period == 0


def _is_intern(li: DialogMobileBillLineItem, employee: DialogMobileEmployee | None) -> bool:
    return bool(employee and employee.cadre and employee.cadre.strip().lower() == "intern")


# The DB column is NUMERIC(12, 2) — max storable absolute value is
# 9999999999.99 (10 digits before the decimal point). Anything at or
# beyond this crashes the whole import with a raw psycopg2 error unless
# guarded here first.
_NUMERIC_12_2_MAX_ABS = Decimal("9999999999.99")


def _safe_numeric_field(mobile_no: str, field_label: str, value, warnings: list[str]):
    """
    Confirmed real: a genuine Dialog .xls export had Data Rental/Data Usage
    values of ±76,669,945,315,413.83 for one connection — almost certainly
    a broken/circular formula in Dialog's own spreadsheet, not anything we
    can infer a correct value for. Rather than crash the entire ~775-row
    import over one connection's one bad field, this resets JUST that
    field to 0 and records a warning, so the connection still gets
    imported normally (never silently dropped from the bill) and the
    issue is visible for manual correction via "Edit line item".
    """
    if value is None:
        return value
    try:
        decimal_value = Decimal(str(value))
    except Exception:
        warnings.append(f"{mobile_no}: {field_label} was not a valid number ({value!r}) — set to 0")
        return 0
    if abs(decimal_value) >= _NUMERIC_12_2_MAX_ABS:
        warnings.append(f"{mobile_no}: {field_label} had an out-of-range value ({decimal_value}) — likely a broken formula in the source file, set to 0")
        return 0
    return value


def _parse_date(value: str | None, fmt: str) -> date | None:
    if not value:
        return None
    return datetime.strptime(value, fmt).date()


def import_bill_file(db: Session, file_path: str, label: str, source_format: str) -> DialogMobileImportResult:
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

    # Relaxed for both source formats: a mismatch against the invoice's own
    # stated total is recorded and shown ("Off by Rs. X") rather than
    # blocking the import — a human reviewing the numbers is better than
    # being locked out of saving the bill entirely. (Previously the PDF
    # path rejected the import outright on any mismatch; that behavior
    # was removed since it's too strict for real-world use.)
    reconciled = stated_total is not None and abs(discrepancy) < Decimal("0.01")

    bill_period = DialogMobileBillPeriod(
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

    corrupted_value_warnings: list[str] = []
    for row in rows:
        mobile_no = row["mobile_no"]
        corrupted_warnings: list[str] = []
        db.add(DialogMobileBillLineItem(
            bill_period_id=bill_period.id,
            mobile_no=mobile_no,
            previous_due_amount=_safe_numeric_field(mobile_no, "Previous Due Amount", row.get("previous_due_amount", 0), corrupted_warnings),
            payments=_safe_numeric_field(mobile_no, "Payments", row.get("payments", 0), corrupted_warnings),
            total_usage_charges=_safe_numeric_field(mobile_no, "Total Usage Charges", row.get("total_usage_charges", 0), corrupted_warnings),
            idd=_safe_numeric_field(mobile_no, "IDD", row.get("idd", 0), corrupted_warnings),
            roaming=_safe_numeric_field(mobile_no, "Roaming", row.get("roaming", 0), corrupted_warnings),
            vas=_safe_numeric_field(mobile_no, "VAS", row.get("vas", 0), corrupted_warnings),
            discounts=_safe_numeric_field(mobile_no, "Discounts", row.get("discounts", 0), corrupted_warnings),
            bill_adjustments_balance_transfers=_safe_numeric_field(mobile_no, "Bill Adjustments/Balance Transfers", row.get("bill_adjustments_balance_transfers", 0), corrupted_warnings),
            commitment_charges=_safe_numeric_field(mobile_no, "Commitment Charges", row.get("commitment_charges", 0), corrupted_warnings),
            late_payment_charges=_safe_numeric_field(mobile_no, "Late Payment Charges", row.get("late_payment_charges", 0), corrupted_warnings),
            add_to_bill_charges=_safe_numeric_field(mobile_no, "Add To Bill Charges", row.get("add_to_bill_charges", 0), corrupted_warnings),
            instalment_plans=_safe_numeric_field(mobile_no, "Instalment Plans", row.get("instalment_plans", 0), corrupted_warnings),
            govt_taxes=_safe_numeric_field(mobile_no, "Government Taxes", row.get("govt_taxes", 0), corrupted_warnings),
            vat=_safe_numeric_field(mobile_no, "VAT", row.get("vat", 0), corrupted_warnings),
            charges_for_bill_period=_safe_numeric_field(mobile_no, "Charges for Bill Period", row.get("charges_for_bill_period", 0), corrupted_warnings),
            total_due_amount=_safe_numeric_field(mobile_no, "Total Due Amount", row.get("total_due_amount", 0), corrupted_warnings),
            # Only present when source_format == "xls" — None for PDF rows
            voice_rental=_safe_numeric_field(mobile_no, "Voice Rental", row.get("voice_rental"), corrupted_warnings),
            voice_usage=_safe_numeric_field(mobile_no, "Voice Usage", row.get("voice_usage"), corrupted_warnings),
            sms=_safe_numeric_field(mobile_no, "SMS", row.get("sms"), corrupted_warnings),
            data_rental=_safe_numeric_field(mobile_no, "Data Rental", row.get("data_rental"), corrupted_warnings),
            data_usage=_safe_numeric_field(mobile_no, "Data Usage", row.get("data_usage"), corrupted_warnings),
        ))
        corrupted_value_warnings.extend(corrupted_warnings)

    db.commit()
    db.refresh(bill_period)

    return DialogMobileImportResult(
        bill_period_id=bill_period.id,
        line_items_imported=len(rows),
        parsed_total_charges_for_bill_period=parsed_total,
        stated_total_charges_for_bill_period=stated_total,
        reconciled=reconciled,
        reconciliation_discrepancy=discrepancy,
        source_format=source_format,
        corrupted_value_warnings=corrupted_value_warnings,
    )


def get_bill_period(db: Session, bill_period_id: uuid.UUID) -> DialogMobileBillPeriod:
    period = db.query(DialogMobileBillPeriod).filter(DialogMobileBillPeriod.id == bill_period_id).first()
    if not period:
        raise HTTPException(status_code=404, detail="Bill period not found")
    return period


def delete_bill_period(db: Session, bill_period_id: uuid.UUID) -> None:
    period = get_bill_period(db, bill_period_id)  # 404 if missing
    db.query(DialogMobileBillLineItem).filter(DialogMobileBillLineItem.bill_period_id == period.id).delete()
    db.delete(period)
    db.commit()


def list_bill_periods(db: Session) -> list[DialogMobileBillPeriod]:
    return db.query(DialogMobileBillPeriod).order_by(DialogMobileBillPeriod.bill_period_start.desc().nullslast()).all()


def get_summary(db: Session, bill_period_id: uuid.UUID) -> list[DialogMobileBillSummaryRow]:
    period = get_bill_period(db, bill_period_id)
    line_items = db.query(DialogMobileBillLineItem).filter(DialogMobileBillLineItem.bill_period_id == period.id).all()
    return _build_summary_rows(db, line_items, bill_period=period)


def get_summary_row_for_line_item(db: Session, line_item_id: uuid.UUID) -> DialogMobileBillSummaryRow:
    line_item = db.query(DialogMobileBillLineItem).filter(DialogMobileBillLineItem.id == line_item_id).first()
    if not line_item:
        raise HTTPException(status_code=404, detail="Bill line item not found")
    period = get_bill_period(db, line_item.bill_period_id)
    # IMPORTANT: must build the summary from EVERY line item in this bill
    # period, not just the one that changed — the eligible headcount, the
    # data bucket pool lookup, and the resulting standard_bucket_cost/vat
    # all depend on seeing every other connection too. Passing only
    # [line_item] here would silently compute those against a list of
    # length 1, giving a wrong bucket_cost the moment a data bucket number
    # is active.
    all_line_items = db.query(DialogMobileBillLineItem).filter(DialogMobileBillLineItem.bill_period_id == period.id).all()
    rows = _build_summary_rows(db, all_line_items, bill_period=period)
    return next(r for r in rows if r.bill_line_item_id == line_item_id)


def _build_summary_rows(db: Session, line_items: list[DialogMobileBillLineItem], bill_period: DialogMobileBillPeriod) -> list[DialogMobileBillSummaryRow]:
    mobile_nos = [li.mobile_no for li in line_items]
    number_rows = (
        db.query(DialogMobileMobileNumber, DialogMobileEmployee)
        .join(DialogMobileEmployee, DialogMobileEmployee.id == DialogMobileMobileNumber.employee_id)
        .filter(DialogMobileMobileNumber.mobile_no.in_(mobile_nos))
        .all()
    )
    employee_by_mobile = {mn.mobile_no: emp for mn, emp in number_rows}
    # project_label lives on DialogMobileMobileNumber, not DialogMobileEmployee
    # — the dict above only kept the Employee half of the join, so this was
    # previously discarded entirely and had no way to reach the summary row.
    project_label_by_mobile = {mn.mobile_no: mn.project_label for mn, emp in number_rows}

    # The "data bucket number" — a specific connection (e.g. the "Data
    # bucket" General line) whose own Charges for Bill Period / VAT ARE the
    # shared pool for the month. When one is selected for this bill period,
    # the standard bucket cost/VAT is derived automatically from it instead
    # of a manually typed rate.
    data_bucket_li = None
    if bill_period.data_bucket_mobile_no:
        data_bucket_li = next(
            (li for li in line_items if li.mobile_no == bill_period.data_bucket_mobile_no), None
        )

    if data_bucket_li is not None:
        # Everyone eligible for the bucket EXCEPT the data bucket
        # connection itself — it's the source of the pool, not a
        # recipient, so it must never be counted in its own denominator.
        eligible_count = sum(
            1
            for li in line_items
            if li.id != data_bucket_li.id
            and not _is_disconnected_this_month(li)
            and not _is_intern(li, employee_by_mobile.get(li.mobile_no))
            and not li.is_bucket_excluded
        )
        if eligible_count > 0:
            # Rounding order matters here and is confirmed against the
            # real source file's own reference "Summary" sheet: Bucket
            # Cost and Bucket VAT are each independently rounded to the
            # cent FIRST, and Bucket Nett is derived by subtracting the
            # two rounded values — NOT computed as its own separately-
            # rounded division. Doing it any other order (e.g. rounding
            # Nett and VAT separately, then summing for Cost) can land a
            # cent off from the reference file on some rows, even though
            # the unrounded math is equivalent.
            standard_bucket_cost = (data_bucket_li.charges_for_bill_period / eligible_count).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            standard_bucket_vat = (data_bucket_li.vat / eligible_count).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            standard_bucket_nett = standard_bucket_cost - standard_bucket_vat
        else:
            # No eligible employees to split the pool across this month —
            # nothing to allocate.
            standard_bucket_cost = Decimal("0")
            standard_bucket_vat = Decimal("0")
            standard_bucket_nett = Decimal("0")
    else:
        # No data bucket number selected for this bill period — nothing
        # to allocate. The "Set bucket rate manually" fallback was removed:
        # a month without a proper data bucket connection now simply
        # results in Rs. 0 bucket cost for everyone until a data bucket
        # number is selected, rather than silently reading a manual figure
        # that's easy to forget was set (or forget was ignored, when a
        # data bucket number WAS active).
        eligible_count = sum(
            1
            for li in line_items
            if not _is_disconnected_this_month(li)
            and not _is_intern(li, employee_by_mobile.get(li.mobile_no))
            and not li.is_bucket_excluded
        )
        standard_bucket_cost = Decimal("0")
        standard_bucket_vat = Decimal("0")
        standard_bucket_nett = Decimal("0")

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
        is_disconnected_this_month = _is_disconnected_this_month(li)

        # Confirmed against a SEPARATE real bill: Interns never get the
        # bucket allocation, even with substantial real usage that
        # month — 100% clean across 82 real Intern rows, zero exceptions
        # either direction. Unlike disconnection, this genuinely can't be
        # inferred from usage — it's tied to cadre, which we already
        # store on the employee.
        is_intern = _is_intern(li, employee)
        is_general_line = bool(employee and employee.is_general_line)
        is_data_bucket_line = data_bucket_li is not None and li.id == data_bucket_li.id

        # The data bucket connection itself is a bucket-excluded number —
        # it's the SOURCE of the pool, not a recipient of it, so it gets
        # zero bucket cost/VAT just like any other excluded connection
        # (is_bucket_excluded is set to True automatically for it in
        # set_data_bucket_number). No special-casing needed here.
        if is_disconnected_this_month or is_intern or li.is_bucket_excluded:
            # General lines are NO LONGER auto-excluded from the bucket
            # just for being a General line — that's now a deliberate
            # per-month decision (li.is_bucket_excluded, set via "Manage
            # bucket exclusion" in the UI, and also set automatically for
            # whichever connection is chosen as the data bucket number
            # itself). Disconnection and Intern status remain fully automatic.
            bucket_cost = Decimal("0")
            bucket_vat = Decimal("0")
        else:
            bucket_cost = standard_bucket_cost
            bucket_vat = standard_bucket_vat
        bucket_nett = bucket_cost - bucket_vat

        net_amount = li.charges_for_bill_period - li.vat
        total = net_amount + bucket_nett
        credit_limit = employee.credit_limit if employee and employee.credit_limit is not None else Decimal("0")

        # Salary Deduction = VAS + Add To Bill Charges + any excess over
        # Credit Limit (Total − Credit Limit, but only when Total actually
        # exceeds it — clamped at 0 rather than allowed to go negative, so
        # someone comfortably under their limit never has this REDUCE their
        # deduction below VAS + Add To Bill Charges). Can be overridden with
        # an exact manual figure via salary_deduction_override, same pattern
        # as approval_override.
        excess_over_credit_limit = max(total - credit_limit, Decimal("0"))
        computed_salary_deduction = li.vas + li.add_to_bill_charges + excess_over_credit_limit
        if li.salary_deduction_override is not None:
            salary_deduction = li.salary_deduction_override
            is_salary_deduction_overridden = True
        else:
            salary_deduction = computed_salary_deduction
            is_salary_deduction_overridden = False

        if li.approval_override:
            need_approval = li.approval_override
            is_overridden = True
        else:
            # Compares against Total (Net Amount + Bucket Nett), not just
            # Net Amount — the bucket portion is a real charge against the
            # employee too, so it belongs in the credit check.
            need_approval = "OK" if total <= credit_limit else "Need Approval"
            is_overridden = False

        results.append(DialogMobileBillSummaryRow(
            bill_line_item_id=li.id,
            mobile_no=li.mobile_no,
            emp_no=employee.emp_no if employee else None,
            name=employee.name if employee else None,
            lob=employee.lob if employee else None,
            lob_code=employee.lob_code if employee else None,
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
            late_payment_charges=li.late_payment_charges,
            net_amount=net_amount,
            bucket_cost=bucket_cost,
            bucket_vat=bucket_vat,
            bucket_nett=bucket_nett,
            total=total,
            salary_deduction=salary_deduction,
            is_salary_deduction_overridden=is_salary_deduction_overridden,
            need_approval=need_approval,
            is_overridden=is_overridden,
            is_general_line=is_general_line,
            is_bucket_excluded=li.is_bucket_excluded,
            is_data_bucket_line=is_data_bucket_line,
            eligible_employee_count=eligible_count,
            standard_bucket_cost=standard_bucket_cost,
            standard_bucket_vat=standard_bucket_vat,
            standard_bucket_nett=standard_bucket_nett,
        ))

    return results


def set_approval_override(db: Session, line_item_id: uuid.UUID, payload: DialogMobileApprovalOverrideInput) -> DialogMobileBillSummaryRow:
    line_item = db.query(DialogMobileBillLineItem).filter(DialogMobileBillLineItem.id == line_item_id).first()
    if not line_item:
        raise HTTPException(status_code=404, detail="Bill line item not found")

    line_item.approval_override = payload.approval_override
    db.commit()
    db.refresh(line_item)
    return get_summary_row_for_line_item(db, line_item_id)


def set_salary_deduction_override(db: Session, line_item_id: uuid.UUID, salary_deduction_override: Decimal | None) -> DialogMobileBillSummaryRow:
    """
    Sets (or clears, if None) an exact manual Salary Deduction figure for
    THIS line item — overrides the computed value (VAS + Add To Bill
    Charges + excess over Credit Limit) entirely, same pattern as
    approval_override. Doesn't affect any other row.
    """
    line_item = db.query(DialogMobileBillLineItem).filter(DialogMobileBillLineItem.id == line_item_id).first()
    if not line_item:
        raise HTTPException(status_code=404, detail="Bill line item not found")

    line_item.salary_deduction_override = salary_deduction_override
    db.commit()
    db.refresh(line_item)
    return get_summary_row_for_line_item(db, line_item_id)


def update_line_item_charges(db: Session, line_item_id: uuid.UUID, payload: DialogMobileLineItemChargeUpdateInput) -> DialogMobileBillSummaryRow:
    """
    Manual correction to a line item's raw charge figures for THIS bill
    period ("Edit line item" in the UI) — used for cases where the real
    billed amount needs a manual fix (e.g. a shared/General line's genuine
    usage charge, or any other connection whose parsed figures are wrong
    for this month). Works for ANY connection in the bill period, not just
    the one selected as the data bucket number. net_amount/total/salary
    deduction/Project Working all recompute automatically on the next
    read, same as everything else in this module.
    """
    line_item = db.query(DialogMobileBillLineItem).filter(DialogMobileBillLineItem.id == line_item_id).first()
    if not line_item:
        raise HTTPException(status_code=404, detail="Bill line item not found")

    line_item.total_usage_charges = payload.total_usage_charges
    line_item.idd = payload.idd
    line_item.roaming = payload.roaming
    line_item.charges_for_bill_period = payload.charges_for_bill_period
    line_item.vat = payload.vat
    line_item.vas = payload.vas
    line_item.add_to_bill_charges = payload.add_to_bill_charges
    line_item.late_payment_charges = payload.late_payment_charges
    db.commit()
    db.refresh(line_item)
    return get_summary_row_for_line_item(db, line_item_id)


def set_bucket_exclusion(db: Session, line_item_id: uuid.UUID, is_bucket_excluded: bool) -> DialogMobileBillSummaryRow:
    """
    Marks/unmarks one connection as excluded from the bucket allocation
    for THIS bill period specifically — a deliberate per-month decision,
    typically used for "General" lines (see DialogMobileEmployee.is_general_line).
    Unlike Mobitel's project cost, this doesn't touch anyone else's
    numbers: the bucket rate here isn't a shared pool split across
    everyone, it's a flat per-connection allocation, so zeroing one
    row's bucket_cost/bucket_vat has zero effect on any other row.
    """
    line_item = db.query(DialogMobileBillLineItem).filter(DialogMobileBillLineItem.id == line_item_id).first()
    if not line_item:
        raise HTTPException(status_code=404, detail="Bill line item not found")

    line_item.is_bucket_excluded = is_bucket_excluded
    db.commit()
    db.refresh(line_item)
    return get_summary_row_for_line_item(db, line_item_id)


def set_data_bucket_number(db: Session, bill_period_id: uuid.UUID, mobile_no: str | None) -> list[DialogMobileBillSummaryRow]:
    """
    Picks (or clears, if mobile_no is None) the connection whose own
    Charges for Bill Period / VAT should be treated as the shared "data
    bucket" pool for THIS bill period — replacing the manual "Set bucket
    rate" entry with an automatic calculation. The chosen connection:
      - is marked is_bucket_excluded so it's dropped out of the normal
        bucket allocation and headcount (it's the source of the pool, not
        a recipient of it)
      - is identified via is_data_bucket_line on the summary row so the
        frontend can pull it out of the main table/sum entirely and show
        it as its own row after the Total row instead (with bucket_cost/
        bucket_vat/bucket_nett all zero on that row, same as any other
        excluded connection — the pool figures come from its own
        charges_for_bill_period/vat fields, not its bucket_cost).
    Switching to a different number (or clearing the selection) un-marks
    whichever connection was previously selected, so it falls back into
    the normal bucket allocation for this month.
    """
    period = get_bill_period(db, bill_period_id)

    if period.data_bucket_mobile_no and period.data_bucket_mobile_no != mobile_no:
        previous = (
            db.query(DialogMobileBillLineItem)
            .filter(
                DialogMobileBillLineItem.bill_period_id == period.id,
                DialogMobileBillLineItem.mobile_no == period.data_bucket_mobile_no,
            )
            .first()
        )
        if previous:
            previous.is_bucket_excluded = False

    if mobile_no:
        new_line_item = (
            db.query(DialogMobileBillLineItem)
            .filter(
                DialogMobileBillLineItem.bill_period_id == period.id,
                DialogMobileBillLineItem.mobile_no == mobile_no,
            )
            .first()
        )
        if not new_line_item:
            raise HTTPException(status_code=404, detail=f"No line item found for mobile number {mobile_no} in this bill period")
        new_line_item.is_bucket_excluded = True

    period.data_bucket_mobile_no = mobile_no
    db.commit()
    return get_summary(db, bill_period_id)