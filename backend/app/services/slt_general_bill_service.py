import logging
import uuid
from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.ingestion.gemini_slt_general_bill_extractor import extract_via_gemini
from app.models.slt_general_account import SltGeneralAccount
from app.models.slt_general_bill_period import SltGeneralBillPeriod
from app.models.slt_general_bill_line_item import SltGeneralBillLineItem
from app.schemas.slt_general_bill import SltGeneralImportOneResult, SltGeneralAccountUpdate

logger = logging.getLogger(__name__)


def _to_decimal(value) -> Decimal | None:
    return Decimal(str(value)) if value is not None else None


def _parse_date(value: str | None):
    return datetime.strptime(value, "%d/%m/%Y").date() if value else None


def _get_or_create_account(db: Session, account_no: str) -> SltGeneralAccount:
    account = db.query(SltGeneralAccount).filter(SltGeneralAccount.account_no == account_no).first()
    if account is None:
        account = SltGeneralAccount(account_no=account_no, label=account_no)
        db.add(account)
        db.flush()
    elif account.is_deleted:
        # A real bill just came in for this account number — that's
        # proof it's active again, so un-hide it. Without this, deleting
        # an account then re-uploading a bill for it would silently keep
        # it hidden from the accounts list forever, even though its
        # bill history was never actually gone.
        account.is_deleted = False
    return account


def import_one_bill(db: Session, pdf_path: str, filename: str, label: str) -> SltGeneralImportOneResult:
    """
    Imports one PDF, fully isolated from the others in the same batch —
    one bad/unreadable file shouldn't block the other 3 from importing.
    """
    if not settings.gemini_api_key:
        return SltGeneralImportOneResult(
            filename=filename, success=False,
            error="GEMINI_API_KEY is not configured. This module requires Gemini — there is no fallback parser.",
        )

    try:
        parsed = extract_via_gemini(pdf_path, settings.gemini_api_key)
    except Exception as exc:
        logger.exception("Gemini extraction failed for SLT general bill: %s", filename)
        return SltGeneralImportOneResult(filename=filename, success=False, error=f"Gemini extraction failed: {exc}")

    if not parsed.get("account_no"):
        return SltGeneralImportOneResult(
            filename=filename, success=False, error="Gemini could not find an Account Number in this PDF",
        )
    if parsed.get("charges_for_period") is None:
        return SltGeneralImportOneResult(
            filename=filename, success=False,
            error="Gemini could not find 'Total Charges for the Period' in this PDF",
        )

    account = _get_or_create_account(db, parsed["account_no"])

    charges_for_period = _to_decimal(parsed["charges_for_period"])

    bill_period = SltGeneralBillPeriod(
        account_id=account.id,
        label=label,
        invoice_no=parsed.get("invoice_no"),
        billing_date=_parse_date(parsed.get("billing_date")),
        period_start=_parse_date(parsed.get("period_start")),
        period_end=_parse_date(parsed.get("period_end")),
        due_date=_parse_date(parsed.get("due_date")),
        balance_bf=_to_decimal(parsed.get("balance_bf")),
        payments_received=_to_decimal(parsed.get("payments_received")),
        charges_for_period=charges_for_period,
        total_payable=_to_decimal(parsed.get("total_payable")),
        extraction_method="gemini",
    )
    db.add(bill_period)
    db.flush()

    line_items_sum = Decimal("0")
    for item in parsed.get("line_items", []):
        amount = _to_decimal(item.get("amount"))
        if amount is None:
            continue
        line_items_sum += amount
        db.add(SltGeneralBillLineItem(
            bill_period_id=bill_period.id,
            description=item.get("description", "").strip() or "(unlabeled)",
            amount=amount,
        ))

    bill_period.line_items_sum = line_items_sum
    bill_period.extraction_discrepancy = line_items_sum - charges_for_period

    db.commit()
    db.refresh(bill_period)

    return SltGeneralImportOneResult(
        filename=filename,
        success=True,
        bill_period_id=bill_period.id,
        account_no=account.account_no,
        account_label=account.label,
        charges_for_period=charges_for_period,
        line_items_sum=line_items_sum,
    )


def list_accounts(db: Session) -> list[SltGeneralAccount]:
    return db.query(SltGeneralAccount).filter(SltGeneralAccount.is_deleted.is_(False)).order_by(SltGeneralAccount.label).all()


def update_account_label(db: Session, account_id: uuid.UUID, payload: SltGeneralAccountUpdate) -> SltGeneralAccount:
    account = db.query(SltGeneralAccount).filter(SltGeneralAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="SLT general account not found")
    account.label = payload.label
    db.commit()
    db.refresh(account)
    return account


def soft_delete_account(db: Session, account_id: uuid.UUID) -> SltGeneralAccount:
    """
    Soft delete only — hides the account from the active management list,
    but its past bill periods keep displaying normally (list_bill_periods
    doesn't filter on is_deleted, so history is never hidden or orphaned).
    If you genuinely need to reuse the same account number later, this
    account row still exists and blocks re-creation — contact support to
    hard-delete a truly junk account with zero bills attached.
    """
    account = db.query(SltGeneralAccount).filter(SltGeneralAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="SLT general account not found")
    account.is_deleted = True
    db.commit()
    db.refresh(account)
    return account


def list_bill_periods(db: Session) -> list[dict]:
    rows = (
        db.query(SltGeneralBillPeriod, SltGeneralAccount)
        .join(SltGeneralAccount, SltGeneralAccount.id == SltGeneralBillPeriod.account_id)
        .order_by(SltGeneralBillPeriod.billing_date.desc().nullslast())
        .all()
    )
    return [_period_with_account(p, a) for p, a in rows]


def _period_with_account(period: SltGeneralBillPeriod, account: SltGeneralAccount) -> dict:
    return {
        "id": period.id,
        "account_id": period.account_id,
        "account_no": account.account_no,
        "account_label": account.label,
        "label": period.label,
        "invoice_no": period.invoice_no,
        "billing_date": period.billing_date,
        "period_start": period.period_start,
        "period_end": period.period_end,
        "due_date": period.due_date,
        "balance_bf": period.balance_bf,
        "payments_received": period.payments_received,
        "charges_for_period": period.charges_for_period,
        "total_payable": period.total_payable,
        "line_items_sum": period.line_items_sum,
        "extraction_discrepancy": period.extraction_discrepancy,
        "extraction_method": period.extraction_method,
        "created_at": period.created_at,
    }


def get_bill_period(db: Session, bill_period_id: uuid.UUID) -> SltGeneralBillPeriod:
    period = db.query(SltGeneralBillPeriod).filter(SltGeneralBillPeriod.id == bill_period_id).first()
    if not period:
        raise HTTPException(status_code=404, detail="SLT general bill period not found")
    return period


def delete_bill_period(db: Session, bill_period_id: uuid.UUID) -> None:
    period = get_bill_period(db, bill_period_id)
    db.query(SltGeneralBillLineItem).filter(SltGeneralBillLineItem.bill_period_id == period.id).delete()
    db.delete(period)
    db.commit()


def get_line_items(db: Session, bill_period_id: uuid.UUID) -> list[SltGeneralBillLineItem]:
    get_bill_period(db, bill_period_id)
    return (
        db.query(SltGeneralBillLineItem)
        .filter(SltGeneralBillLineItem.bill_period_id == bill_period_id)
        .order_by(SltGeneralBillLineItem.created_at)
        .all()
    )