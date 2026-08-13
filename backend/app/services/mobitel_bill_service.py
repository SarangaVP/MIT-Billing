import logging
import uuid
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.ingestion.mobitel_pdf_parser import parse_mobitel_bill
from app.ingestion.gemini_pdf_extractor import extract_via_gemini
from app.ingestion.mobitel_portal_parser import parse_portal_sheet
from app.models.mobitel_bill_period import MobitelBillPeriod
from app.models.mobitel_bill_line_item import MobitelBillLineItem
from app.models.mobitel_employee import MobitelEmployee
from app.models.mobitel_connection import MobitelConnection, MobitelConnectionStatus
from app.schemas.mobitel_bill import MobitelImportResult

logger = logging.getLogger(__name__)


def _detect_date_order(sample_date_str: str | None) -> str:
    """
    Determines whether THIS bill's dates are DD/MM/YYYY or MM/DD/YYYY, using
    whichever field is unambiguous (one part > 12). Verified against real
    data that a bill's OTHER dates (due date, period dates) follow the same
    convention as its Bill Date — resolving each field's ambiguity
    independently (rather than detecting once and applying consistently)
    previously gave a wrong due date: June'26's real gap from bill date to
    due date is 15 days; treating July'26's ambiguous "08/09/2026" due date
    independently defaulted to DD/MM and produced a 45-day gap, which is
    implausible — the correct MM/DD reading (matching this month's Bill
    Date format) gives 15 days, consistent with June's real pattern.

    Defaults to "DMY" only if truly no signal is available anywhere.
    """
    if sample_date_str:
        parts = sample_date_str.split("/")
        if len(parts) == 3:
            try:
                a, b = int(parts[0]), int(parts[1])
                # If the SECOND part exceeds 12, it can't be a month under
                # DD/MM — so this must be MM/DD (a=month, b=day).
                if b > 12:
                    return "MDY"
                # If the FIRST part exceeds 12, it can't be a month under
                # MM/DD — so this must be DD/MM (a=day, b=month).
                if a > 12:
                    return "DMY"
            except ValueError:
                pass
    return "DMY"


def _parse_full_date_with_order(date_str: str | None, order: str) -> date | None:
    if not date_str:
        return None
    parts = date_str.split("/")
    if len(parts) != 3:
        return None
    try:
        a, b, year = int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError:
        return None
    day, month = (b, a) if order == "MDY" else (a, b)
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _parse_dm_with_order(dm_str: str | None, order: str, year: int) -> date | None:
    if not dm_str:
        return None
    parts = dm_str.split("/")
    if len(parts) != 2:
        return None
    try:
        a, b = int(parts[0]), int(parts[1])
    except ValueError:
        return None
    day, month = (b, a) if order == "MDY" else (a, b)
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _resolve_period_dates(
    bill_date: date, start_dm: str | None, end_dm: str | None, order: str
) -> tuple[date | None, date | None]:
    """
    The bill only gives period dates without a year. Anchors the year
    using bill_date, handling the one edge case where the period starts
    in the December of the previous year (e.g. bill in Jan, period starts
    in Dec).
    """
    if not start_dm or not end_dm:
        return None, None

    end_date = _parse_dm_with_order(end_dm, order, bill_date.year)
    if end_date is None:
        return None, None

    start_date = _parse_dm_with_order(start_dm, order, bill_date.year)
    if start_date is not None and start_date.month > end_date.month:
        start_date = _parse_dm_with_order(start_dm, order, bill_date.year - 1)

    return start_date, end_date


def _extract_bill_fields(pdf_path: str) -> tuple[dict, str]:
    """
    Gemini is the PRIMARY extraction method — it reads the actual PDF
    content directly, so it keeps working even if Mobitel changes the
    bill's wording or layout, unlike the regex parser. Falls back to the
    regex parser automatically if Gemini raises for any reason (missing/
    invalid API key, network error, rate limit, malformed response) or
    returns incomplete data (missing bucket/vat).

    Returns (parsed_fields, extraction_method) so the caller can always
    record which method actually produced a given bill's numbers.
    """
    if settings.gemini_api_key:
        try:
            parsed = extract_via_gemini(pdf_path, settings.gemini_api_key)
            if parsed.get("bucket") is not None and parsed.get("vat") is not None:
                return parsed, "gemini"
            logger.warning("Gemini extraction returned incomplete data (missing bucket/vat) — falling back to regex")
        except Exception:
            logger.exception("Gemini extraction failed — falling back to regex parser")
    else:
        logger.info("No GEMINI_API_KEY configured — using regex parser directly")

    return parse_mobitel_bill(pdf_path), "regex_fallback"


def import_mobitel_bill(db: Session, pdf_path: str, label: str, portal_path: str | None = None) -> MobitelImportResult:
    parsed, extraction_method = _extract_bill_fields(pdf_path)
    portal_data = parse_portal_sheet(portal_path) if portal_path else {}

    if parsed["bucket"] is None or parsed["vat"] is None:
        raise HTTPException(
            status_code=422,
            detail=(
                "Could not find 'Total Charge for the Month' or 'VAT' in this PDF, even after trying both "
                "AI and regex extraction — check the file format"
            ),
        )

    bucket = Decimal(str(parsed["bucket"]))
    vat = Decimal(str(parsed["vat"]))
    net = bucket - vat

    date_order = _detect_date_order(parsed["bill_date"])
    bill_date = _parse_full_date_with_order(parsed["bill_date"], date_order)
    due_date = _parse_full_date_with_order(parsed["due_date"], date_order)
    period_start, period_end = (
        _resolve_period_dates(bill_date, parsed["period_start_dm"], parsed["period_end_dm"], date_order)
        if bill_date
        else (None, None)
    )

    active_connections = (
        db.query(MobitelConnection)
        .join(MobitelEmployee, MobitelEmployee.id == MobitelConnection.employee_id)
        .filter(
            MobitelConnection.status == MobitelConnectionStatus.active,
            MobitelConnection.is_deleted.is_(False),
            MobitelEmployee.is_deleted.is_(False),
            MobitelEmployee.is_pool.is_(False),
        )
        .all()
    )

    unmatched_in_portal_sheet: list[str] = []
    if portal_data:
        # Same fix as Dialog Data Bucket: the Portal sheet is the
        # authoritative record of who was ACTUALLY billed this specific
        # month. Our own roster's "active" status alone can overcount
        # (e.g. someone marked active who was genuinely dormant/unbilled
        # that month) — restrict to the intersection of "active in our
        # roster" AND "actually present in this month's Portal sheet".
        our_mobile_nos = {c.mobile_no for c in active_connections}
        active_connections = [c for c in active_connections if c.mobile_no in portal_data]
        unmatched_in_portal_sheet = sorted(set(portal_data.keys()) - our_mobile_nos)

    users = len(active_connections)
    if users == 0:
        raise HTTPException(status_code=422, detail="No active Mobitel connections to split this bill across")

    # Static IP cost is NOT a persistent rate anymore — every employee
    # starts at 0 for a newly imported bill. It's set per-bill-period,
    # per-employee, directly from the Bill Summary page (see
    # update_static_ip_cost below), which also recalculates the split.
    per_user_cost = (net / users).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

    bill_period = MobitelBillPeriod(
        label=label,
        bill_no=parsed["bill_no"],
        account_no=parsed["account_no"],
        bill_date=bill_date,
        due_date=due_date,
        period_start=period_start,
        period_end=period_end,
        arrears=Decimal(str(parsed["arrears"])) if parsed["arrears"] is not None else None,
        bucket_total=bucket,
        vat=vat,
        net=net,
        total_payable=Decimal(str(parsed["total_payable"])) if parsed["total_payable"] is not None else None,
        users_count=users,
        per_user_cost=per_user_cost,
        extraction_method=extraction_method,
    )
    db.add(bill_period)
    db.flush()

    line_total = Decimal("0")
    for connection in active_connections:
        data_cost = per_user_cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        line_total += data_cost

        usage = portal_data.get(connection.mobile_no, {})

        db.add(MobitelBillLineItem(
            bill_period_id=bill_period.id,
            connection_id=connection.id,
            data_cost=data_cost,
            static_ip_cost=Decimal("0"),
            total=data_cost,
            imsi_number=usage.get("imsi_number"),
            data_volume_mb=usage.get("data_volume_mb"),
            available_data_volume_mb=usage.get("available_data_volume_mb"),
            utilized_data_volume_mb=usage.get("utilized_data_volume_mb"),
            daily_limit_mb=usage.get("daily_limit_mb"),
            utilized_daily_limit_mb=usage.get("utilized_daily_limit_mb"),
            member_status=usage.get("member_status"),
            top_up_mb=usage.get("top_up_mb"),
            utilized_topup_mb=usage.get("utilized_topup_mb"),
        ))

    discrepancy = line_total - net
    reconciled = abs(discrepancy) < Decimal("0.01")

    bill_period.reconciled = reconciled
    bill_period.reconciliation_discrepancy = discrepancy

    db.commit()
    db.refresh(bill_period)

    return MobitelImportResult(
        bill_period_id=bill_period.id,
        line_items_created=users,
        users_count=users,
        net=net,
        per_user_cost=per_user_cost,
        parsed_total=line_total,
        reconciled=reconciled,
        reconciliation_discrepancy=discrepancy,
        extraction_method=extraction_method,
        unmatched_in_portal_sheet=unmatched_in_portal_sheet,
    )


def list_bill_periods(db: Session) -> list[MobitelBillPeriod]:
    return db.query(MobitelBillPeriod).order_by(MobitelBillPeriod.bill_date.desc().nullslast()).all()


def get_bill_period(db: Session, bill_period_id: uuid.UUID) -> MobitelBillPeriod:
    period = db.query(MobitelBillPeriod).filter(MobitelBillPeriod.id == bill_period_id).first()
    if not period:
        raise HTTPException(status_code=404, detail="Mobitel bill period not found")
    return period


def delete_bill_period(db: Session, bill_period_id: uuid.UUID) -> None:
    period = get_bill_period(db, bill_period_id)  # 404 if missing
    db.query(MobitelBillLineItem).filter(MobitelBillLineItem.bill_period_id == period.id).delete()
    db.delete(period)
    db.commit()


def get_summary(db: Session, bill_period_id: uuid.UUID) -> list[dict]:
    get_bill_period(db, bill_period_id)  # 404 if missing
    rows = (
        db.query(MobitelBillLineItem, MobitelConnection, MobitelEmployee)
        .join(MobitelConnection, MobitelConnection.id == MobitelBillLineItem.connection_id)
        .join(MobitelEmployee, MobitelEmployee.id == MobitelConnection.employee_id)
        .filter(MobitelBillLineItem.bill_period_id == bill_period_id)
        .order_by(MobitelEmployee.name)
        .all()
    )
    return [
        {
            "id": li.id,
            "connection_id": li.connection_id,
            "emp_no": emp.emp_no,
            "name": emp.name,
            "lob": emp.lob,
            "lob_code": emp.lob_code,
            "mobile_no": conn.mobile_no,
            "data_cost": li.data_cost,
            "static_ip_cost": li.static_ip_cost,
            "is_project_cost": li.is_project_cost,
            "project_cost_amount": li.project_cost_amount,
            "total": li.total,
            "imsi_number": li.imsi_number,
            "data_volume_mb": li.data_volume_mb,
            "available_data_volume_mb": li.available_data_volume_mb,
            "utilized_data_volume_mb": li.utilized_data_volume_mb,
            "daily_limit_mb": li.daily_limit_mb,
            "utilized_daily_limit_mb": li.utilized_daily_limit_mb,
            "member_status": li.member_status,
            "top_up_mb": li.top_up_mb,
            "utilized_topup_mb": li.utilized_topup_mb,
        }
        for li, conn, emp in rows
    ]


def _recalculate_period(db: Session, bill_period: MobitelBillPeriod) -> None:
    """
    Shared by update_static_ip_cost and update_project_cost — both change a
    per-connection cost that affects everyone else's split, so both need
    the identical whole-period recompute.

    Project-cost items (is_project_cost=True) are excluded from BOTH the
    shared pool and the headcount — confirmed against a real bill where
    2 people had a manually-set data cost with no detectable rule behind
    it: their amounts were subtracted from Net, and they were removed
    from Users, before the remaining people split what's left evenly.
    Verified this exact reconstruction reproduces the real file's numbers
    to the cent (net=280,209.32, 2 project costs totaling 15,060.75, one
    static IP of 1,500 -> per-user 2,215.53 across the remaining 119).
    """
    all_items = (
        db.query(MobitelBillLineItem)
        .filter(MobitelBillLineItem.bill_period_id == bill_period.id)
        .all()
    )
    project_items = [item for item in all_items if item.is_project_cost]
    normal_items = [item for item in all_items if not item.is_project_cost]

    users = len(normal_items)
    if users == 0:
        raise HTTPException(status_code=422, detail="Every connection on this bill is marked project-cost — nothing left to split")

    total_static_ip = sum((item.static_ip_cost or Decimal("0")) for item in all_items)
    total_project_cost = sum((item.project_cost_amount or Decimal("0")) for item in project_items)
    net = bill_period.net or Decimal("0")

    per_user_cost = ((net - total_static_ip - total_project_cost) / users).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

    line_total = Decimal("0")
    for item in normal_items:
        item.data_cost = per_user_cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        item.total = (item.data_cost + (item.static_ip_cost or Decimal("0"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        line_total += item.total

    for item in project_items:
        item.data_cost = (item.project_cost_amount or Decimal("0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        item.total = (item.data_cost + (item.static_ip_cost or Decimal("0"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        line_total += item.total

    discrepancy = line_total - net
    bill_period.per_user_cost = per_user_cost
    bill_period.reconciled = abs(discrepancy) < Decimal("0.01")
    bill_period.reconciliation_discrepancy = discrepancy


def update_static_ip_cost(db: Session, line_item_id: uuid.UUID, new_cost: Decimal) -> list[dict]:
    """
    Sets one line item's static IP cost for THIS bill period specifically,
    then recalculates the whole period: since the per-user data cost is
    (Net - total static IP - total project cost) / Users, changing any one
    connection's static IP cost changes the split for everyone else too.
    """
    line_item = db.query(MobitelBillLineItem).filter(MobitelBillLineItem.id == line_item_id).first()
    if not line_item:
        raise HTTPException(status_code=404, detail="Bill line item not found")

    bill_period = get_bill_period(db, line_item.bill_period_id)
    line_item.static_ip_cost = new_cost
    db.flush()

    _recalculate_period(db, bill_period)
    db.commit()

    return get_summary(db, bill_period.id)


def update_project_cost(db: Session, line_item_id: uuid.UUID, is_project_cost: bool, project_cost_amount: Decimal | None) -> list[dict]:
    """
    Marks (or unmarks) one connection as having a manually-set project cost
    for THIS bill period — used when a real charge is a known specific
    amount with no detectable automated rule behind it (confirmed real
    cases: an SLA-based rate, and one with no discernible pattern at
    all). Excludes that connection from both the shared pool and the
    headcount for everyone else's equal split, then recalculates.
    """
    if is_project_cost and project_cost_amount is None:
        raise HTTPException(status_code=422, detail="project_cost_amount is required when is_project_cost is true")

    line_item = db.query(MobitelBillLineItem).filter(MobitelBillLineItem.id == line_item_id).first()
    if not line_item:
        raise HTTPException(status_code=404, detail="Bill line item not found")

    bill_period = get_bill_period(db, line_item.bill_period_id)
    line_item.is_project_cost = is_project_cost
    line_item.project_cost_amount = project_cost_amount if is_project_cost else None
    db.flush()

    _recalculate_period(db, bill_period)
    db.commit()

    return get_summary(db, bill_period.id)