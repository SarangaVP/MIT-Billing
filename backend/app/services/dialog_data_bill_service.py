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

    active_connections = (
        db.query(DialogDataConnection)
        .join(DialogDataEmployee, DialogDataEmployee.id == DialogDataConnection.employee_id)
        .filter(
            DialogDataConnection.status == DialogDataConnectionStatus.active,
            DialogDataConnection.is_deleted.is_(False),
            DialogDataEmployee.is_deleted.is_(False),
        )
        .all()
    )
    users = len(active_connections)
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
    for connection in active_connections:
        cost = per_user_cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        line_total += cost

        usage = usage_data.get(connection.connection_no, {})

        db.add(DialogDataBillLineItem(
            bill_period_id=bill_period.id,
            connection_id=connection.id,
            cost=cost,
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
    rows = (
        db.query(DialogDataBillLineItem, DialogDataConnection, DialogDataEmployee)
        .join(DialogDataConnection, DialogDataConnection.id == DialogDataBillLineItem.connection_id)
        .join(DialogDataEmployee, DialogDataEmployee.id == DialogDataConnection.employee_id)
        .filter(DialogDataBillLineItem.bill_period_id == bill_period_id)
        .order_by(DialogDataEmployee.name)
        .all()
    )
    return [
        {
            "id": li.id,
            "connection_id": li.connection_id,
            "emp_no": emp.emp_no,
            "name": emp.name,
            "team": emp.team,
            "connection_no": conn.connection_no,
            "cost": li.cost,
            "allocation_gb": li.allocation_gb,
            "usage_gb": li.usage_gb,
            "remaining_gb": li.remaining_gb,
            "pay_go_status": li.pay_go_status,
            "bill_cycle": li.bill_cycle,
        }
        for li, conn, emp in rows
    ]