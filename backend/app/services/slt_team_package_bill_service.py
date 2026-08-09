import logging
import uuid
from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.ingestion.gemini_slt_team_package_extractor import extract_via_gemini
from app.ingestion.slt_summary_excel_parser import parse_summary_excel
from app.models.slt_team_package_bill_period import SltTeamPackageBillPeriod
from app.models.slt_team_package_bill_line_item import SltTeamPackageBillLineItem
from app.schemas.slt_bill import SltTeamPackageImportResult

logger = logging.getLogger(__name__)


def _to_decimal(value) -> Decimal | None:
    return Decimal(str(value)) if value is not None else None


def import_team_package_bill(db: Session, pdf_path: str, excel_path: str, label: str) -> SltTeamPackageImportResult:
    """
    Both the PDF and the Summary Excel are REQUIRED every month — the
    Excel is uploaded fresh each time and IS the source of that month's
    employee/package allocation, not a persistent seeded roster. This
    means each bill period is fully self-contained: re-uploading a
    corrected Excel for the same month just creates a new period, same
    "never silently overwrite" pattern used everywhere else in this app.
    """
    if not settings.gemini_api_key:
        raise HTTPException(
            status_code=422,
            detail="GEMINI_API_KEY is not configured. This module requires Gemini — there is no fallback parser.",
        )

    try:
        parsed = extract_via_gemini(pdf_path, settings.gemini_api_key)
    except Exception as exc:
        logger.exception("Gemini extraction failed for SLT team package bill")
        raise HTTPException(
            status_code=422,
            detail=f"Gemini extraction failed and this module has no fallback parser: {exc}",
        )

    if parsed.get("charges_for_period") is None:
        raise HTTPException(
            status_code=422,
            detail="Gemini could not find 'Total Charges for the Period' in this PDF — check the file",
        )

    try:
        employee_rows = parse_summary_excel(excel_path)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not parse the Summary Excel file: {exc}")

    if not employee_rows:
        raise HTTPException(status_code=422, detail="No employee rows found in the Summary sheet of this Excel file")

    charges_for_period = _to_decimal(parsed["charges_for_period"])
    cess = _to_decimal(parsed.get("cess")) or Decimal("0")
    sscl = _to_decimal(parsed.get("sscl")) or Decimal("0")
    vat = _to_decimal(parsed.get("vat")) or Decimal("0")

    billing_date = (
        datetime.strptime(parsed["billing_date"], "%d/%m/%Y").date() if parsed.get("billing_date") else None
    )
    period_start = (
        datetime.strptime(parsed["period_start"], "%d/%m/%Y").date() if parsed.get("period_start") else None
    )
    period_end = (
        datetime.strptime(parsed["period_end"], "%d/%m/%Y").date() if parsed.get("period_end") else None
    )
    due_date = datetime.strptime(parsed["due_date"], "%d/%m/%Y").date() if parsed.get("due_date") else None

    users = len(employee_rows)
    package_sum = sum((Decimal(str(r["package_price"])) for r in employee_rows), Decimal("0"))

    bill_period = SltTeamPackageBillPeriod(
        label=label,
        account_no=parsed.get("account_no"),
        invoice_no=parsed.get("invoice_no"),
        billing_date=billing_date,
        period_start=period_start,
        period_end=period_end,
        due_date=due_date,
        balance_bf=_to_decimal(parsed.get("balance_bf")),
        payments_received=_to_decimal(parsed.get("payments_received")),
        cess=cess,
        sscl=sscl,
        vat=vat,
        charges_for_period=charges_for_period,
        total_payable=_to_decimal(parsed.get("total_payable")),
        users_count=users,
        package_sum=package_sum,
        extraction_method="gemini",
    )
    db.add(bill_period)
    db.flush()

    for row in employee_rows:
        db.add(SltTeamPackageBillLineItem(
            bill_period_id=bill_period.id,
            name=row["name"],
            team=row["team"],
            lob_code=row["lob_code"],
            package_name=row["package_name"],
            package_price=Decimal(str(row["package_price"])),
        ))

    # Reconciliation: sum(package prices) + Cess + SSCL + VAT should equal
    # the PDF's stated Total Charges for the Period. "Never block" policy,
    # same as every other module — always save, always report the exact
    # gap, since a small drift here can be a real-world manual-adjustment
    # nuance (confirmed the source Excel itself has shown this before),
    # not necessarily a sign of a broken calculation.
    computed_total = package_sum + cess + sscl + vat
    discrepancy = computed_total - charges_for_period
    reconciled = abs(discrepancy) < Decimal("0.01")

    bill_period.reconciled = reconciled
    bill_period.reconciliation_discrepancy = discrepancy

    db.commit()
    db.refresh(bill_period)

    return SltTeamPackageImportResult(
        bill_period_id=bill_period.id,
        line_items_created=users,
        users_count=users,
        package_sum=package_sum,
        charges_for_period=charges_for_period,
        computed_total=computed_total,
        reconciled=reconciled,
        reconciliation_discrepancy=discrepancy,
    )


def list_bill_periods(db: Session) -> list[SltTeamPackageBillPeriod]:
    return db.query(SltTeamPackageBillPeriod).order_by(SltTeamPackageBillPeriod.billing_date.desc().nullslast()).all()


def get_bill_period(db: Session, bill_period_id: uuid.UUID) -> SltTeamPackageBillPeriod:
    period = db.query(SltTeamPackageBillPeriod).filter(SltTeamPackageBillPeriod.id == bill_period_id).first()
    if not period:
        raise HTTPException(status_code=404, detail="SLT team package bill period not found")
    return period


def delete_bill_period(db: Session, bill_period_id: uuid.UUID) -> None:
    period = get_bill_period(db, bill_period_id)
    db.query(SltTeamPackageBillLineItem).filter(SltTeamPackageBillLineItem.bill_period_id == period.id).delete()
    db.delete(period)
    db.commit()


def get_summary(db: Session, bill_period_id: uuid.UUID) -> list[SltTeamPackageBillLineItem]:
    get_bill_period(db, bill_period_id)
    return (
        db.query(SltTeamPackageBillLineItem)
        .filter(SltTeamPackageBillLineItem.bill_period_id == bill_period_id)
        .order_by(SltTeamPackageBillLineItem.name)
        .all()
    )