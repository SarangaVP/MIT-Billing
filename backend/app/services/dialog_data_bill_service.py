import logging
import uuid
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.ingestion.dialog_data_pdf_parser import parse_dialog_data_bill
from app.ingestion.gemini_dialog_data_extractor import extract_via_gemini
from app.ingestion.dialog_data_bill_sheet_parser import parse_bill_sheet
from app.models.dialog_data_bill_period import DialogDataBillPeriod
from app.models.dialog_data_bill_line_item import DialogDataBillLineItem
from app.models.dialog_data_employee import DialogDataEmployee
from app.models.dialog_data_connection import DialogDataConnection, DialogDataConnectionStatus
from app.schemas.dialog_data_bill import DialogDataImportResult

logger = logging.getLogger(__name__)


def _extract_bill_fields(pdf_path: str) -> tuple[dict, str]:
    """
    Gemini is the PRIMARY extraction method — same AI-first, regex-fallback
    policy as Mobitel. Falls back automatically if Gemini raises for any
    reason, or returns incomplete data (missing total/vat).
    """
    if settings.gemini_api_key:
        try:
            parsed = extract_via_gemini(pdf_path, settings.gemini_api_key)
            if parsed.get("total") is not None and parsed.get("vat") is not None:
                return parsed, "gemini"
            logger.warning("Gemini extraction returned incomplete data (missing total/vat) — falling back to regex")
        except Exception:
            logger.exception("Gemini extraction failed — falling back to regex parser")
    else:
        logger.info("No GEMINI_API_KEY configured — using regex parser directly")

    return parse_dialog_data_bill(pdf_path), "regex_fallback"


def import_dialog_data_bill(
    db: Session, pdf_path: str, label: str, bill_sheet_path: str | None = None
) -> DialogDataImportResult:
    parsed, extraction_method = _extract_bill_fields(pdf_path)
    usage_data = parse_bill_sheet(bill_sheet_path) if bill_sheet_path else {}

    if parsed["total"] is None or parsed["vat"] is None:
        raise HTTPException(
            status_code=422,
            detail=(
                "Could not find 'Total Charges for Bill Period' or 'VAT' in this PDF, even after trying "
                "both AI and regex extraction — check the file format"
            ),
        )

    total = Decimal(str(parsed["total"]))
    vat = Decimal(str(parsed["vat"]))
    net = total - vat

    invoice_date = datetime.strptime(parsed["invoice_date"], "%d/%m/%Y").date() if parsed["invoice_date"] else None
    period_start = datetime.strptime(parsed["period_start"], "%d/%m/%Y").date() if parsed["period_start"] else None
    period_end = datetime.strptime(parsed["period_end"], "%d/%m/%Y").date() if parsed["period_end"] else None

    active_connections_with_employee = (
        db.query(DialogDataConnection, DialogDataEmployee)
        .join(DialogDataEmployee, DialogDataEmployee.id == DialogDataConnection.employee_id)
        .filter(
            DialogDataConnection.status == DialogDataConnectionStatus.active,
            DialogDataConnection.is_deleted.is_(False),
            DialogDataEmployee.is_deleted.is_(False),
        )
        .all()
    )

    unmatched_in_bill_sheet: list[str] = []
    if usage_data:
        # The Bill sheet is the authoritative record of who was ACTUALLY
        # billed this specific month — confirmed against real data that
        # our own roster can include connections that were added but not
        # yet activated, or already terminated but not yet removed. Using
        # our roster's blanket "active" status alone overcounts; restrict
        # to the intersection of "active in our roster" AND "actually
        # billed this month per the Bill sheet".
        our_connection_nos = {c.connection_no for c, e in active_connections_with_employee}
        active_connections_with_employee = [
            (c, e) for c, e in active_connections_with_employee if c.connection_no in usage_data
        ]
        unmatched_in_bill_sheet = sorted(set(usage_data.keys()) - our_connection_nos)

    users = len(active_connections_with_employee)
    if users == 0:
        raise HTTPException(status_code=422, detail="No active Dialog Data Bucket connections to split this bill across")

    per_user_cost = (net / users).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

    bill_period = DialogDataBillPeriod(
        label=label,
        invoice_no=parsed["invoice_no"],
        mobile_no=parsed["mobile_no"],
        invoice_date=invoice_date,
        period_start=period_start,
        period_end=period_end,
        data_charge=Decimal(str(parsed["data_charge"])) if parsed["data_charge"] is not None else None,
        govt_taxes=Decimal(str(parsed["govt_taxes"])) if parsed["govt_taxes"] is not None else None,
        vat=vat,
        total=total,
        net=net,
        users_count=users,
        per_user_cost=per_user_cost,
        extraction_method=extraction_method,
    )
    db.add(bill_period)
    db.flush()

    line_total = Decimal("0")
    for connection, employee in active_connections_with_employee:
        cost = per_user_cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        line_total += cost

        usage = usage_data.get(connection.connection_no, {})

        # Snapshot the employee identity NOW, at import time — see the
        # model's comment on why this is never re-derived from a live
        # join later.
        db.add(DialogDataBillLineItem(
            bill_period_id=bill_period.id,
            connection_id=connection.id,
            cost=cost,
            connection_no_snapshot=connection.connection_no,
            emp_no_snapshot=employee.emp_no if employee else None,
            name_snapshot=employee.name if employee else None,
            team_snapshot=employee.team if employee else None,
            lob_code_snapshot=employee.lob_code if employee else None,
            allocation_gb=usage.get("allocation_gb"),
            usage_gb=usage.get("usage_gb"),
            remaining_gb=usage.get("remaining_gb"),
            pay_go_status=usage.get("pay_go_status"),
            bill_cycle=usage.get("bill_cycle"),
        ))

    discrepancy = line_total - net
    reconciled = abs(discrepancy) < Decimal("0.01")

    bill_period.reconciled = reconciled
    bill_period.reconciliation_discrepancy = discrepancy

    db.commit()
    db.refresh(bill_period)

    return DialogDataImportResult(
        bill_period_id=bill_period.id,
        line_items_created=users,
        users_count=users,
        net=net,
        per_user_cost=per_user_cost,
        parsed_total=line_total,
        reconciled=reconciled,
        reconciliation_discrepancy=discrepancy,
        extraction_method=extraction_method,
        unmatched_in_bill_sheet=unmatched_in_bill_sheet,
    )


def list_bill_periods(db: Session) -> list[DialogDataBillPeriod]:
    return db.query(DialogDataBillPeriod).order_by(DialogDataBillPeriod.invoice_date.desc().nullslast()).all()


def get_bill_period(db: Session, bill_period_id: uuid.UUID) -> DialogDataBillPeriod:
    period = db.query(DialogDataBillPeriod).filter(DialogDataBillPeriod.id == bill_period_id).first()
    if not period:
        raise HTTPException(status_code=404, detail="Dialog Data Bucket bill period not found")
    return period


def delete_bill_period(db: Session, bill_period_id: uuid.UUID) -> None:
    period = get_bill_period(db, bill_period_id)
    db.query(DialogDataBillLineItem).filter(DialogDataBillLineItem.bill_period_id == period.id).delete()
    db.delete(period)
    db.commit()


def get_summary(db: Session, bill_period_id: uuid.UUID) -> list[dict]:
    get_bill_period(db, bill_period_id)
    # Reads the frozen snapshot fields on each line item — NOT a live join
    # to DialogDataConnection/DialogDataEmployee. This is deliberate: a
    # connection's employee_id can be reassigned later (Master sheet sync
    # resolving an EMP No conflict, an employee transferring their number
    # to someone else), and this bill must keep showing who it was
    # actually billed to at the time it was created, regardless of any
    # later reassignment. See the model's comment for the full reasoning.
    items = (
        db.query(DialogDataBillLineItem)
        .filter(DialogDataBillLineItem.bill_period_id == bill_period_id)
        .order_by(DialogDataBillLineItem.name_snapshot)
        .all()
    )
    return [
        {
            "id": li.id,
            "connection_id": li.connection_id,
            "emp_no": li.emp_no_snapshot,
            "name": li.name_snapshot,
            "team": li.team_snapshot,
            "lob_code": li.lob_code_snapshot,
            "connection_no": li.connection_no_snapshot,
            "cost": li.cost,
            "is_project_cost": li.is_project_cost,
            "project_cost_amount": li.project_cost_amount,
            "allocation_gb": li.allocation_gb,
            "usage_gb": li.usage_gb,
            "remaining_gb": li.remaining_gb,
            "pay_go_status": li.pay_go_status,
            "bill_cycle": li.bill_cycle,
        }
        for li in items
    ]


def _recalculate_period(db: Session, bill_period: DialogDataBillPeriod) -> None:
    """
    Same behavior as Mobitel's recalculation: project-cost items
    (is_project_cost=True) are excluded from BOTH the shared pool and the
    headcount — their amounts are subtracted from Net, and they're
    removed from Users, before the remaining connections split what's
    left evenly.
    """
    all_items = (
        db.query(DialogDataBillLineItem)
        .filter(DialogDataBillLineItem.bill_period_id == bill_period.id)
        .all()
    )
    project_items = [item for item in all_items if item.is_project_cost]
    normal_items = [item for item in all_items if not item.is_project_cost]

    users = len(normal_items)
    if users == 0:
        raise HTTPException(status_code=422, detail="Every connection on this bill is marked project-cost — nothing left to split")

    total_project_cost = sum((item.project_cost_amount or Decimal("0")) for item in project_items)
    net = bill_period.net or Decimal("0")

    per_user_cost = ((net - total_project_cost) / users).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

    line_total = Decimal("0")
    for item in normal_items:
        item.cost = per_user_cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        line_total += item.cost

    for item in project_items:
        item.cost = (item.project_cost_amount or Decimal("0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        line_total += item.cost

    discrepancy = line_total - net
    bill_period.per_user_cost = per_user_cost
    bill_period.reconciled = abs(discrepancy) < Decimal("0.01")
    bill_period.reconciliation_discrepancy = discrepancy


def update_project_cost(db: Session, line_item_id: uuid.UUID, is_project_cost: bool, project_cost_amount: Decimal | None) -> list[dict]:
    """
    Marks (or unmarks) one connection as having a manually-set project cost
    for THIS bill period — same behavior as Mobitel's project cost.
    Excludes that connection from both the shared pool and the headcount
    for everyone else's equal split, then recalculates.
    """
    if is_project_cost and project_cost_amount is None:
        raise HTTPException(status_code=422, detail="project_cost_amount is required when is_project_cost is true")

    line_item = db.query(DialogDataBillLineItem).filter(DialogDataBillLineItem.id == line_item_id).first()
    if not line_item:
        raise HTTPException(status_code=404, detail="Bill line item not found")

    bill_period = get_bill_period(db, line_item.bill_period_id)
    line_item.is_project_cost = is_project_cost
    line_item.project_cost_amount = project_cost_amount if is_project_cost else None
    db.flush()

    _recalculate_period(db, bill_period)
    db.commit()

    return get_summary(db, bill_period.id)