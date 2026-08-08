import uuid

from sqlalchemy import Column, String, Date, Numeric, Boolean, DateTime, ForeignKey, func

from app.database import Base
from app.types import GUID


class SltGeneralBillPeriod(Base):
    """
    One imported monthly bill for one of the 4 "general" SLT accounts.
    No per-employee split — just tracked and displayed as-is. Itemized
    charges live on SltGeneralBillLineItem, since these vary a lot in
    shape between accounts (broadband, static IP, voice lines, PeoTV,
    business internet — confirmed real examples of each).
    """

    __tablename__ = "slt_general_bill_periods"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    account_id = Column(GUID, ForeignKey("slt_general_accounts.id"), nullable=False, index=True)

    label = Column(String, nullable=False)          # e.g. "June 2026"
    invoice_no = Column(String, nullable=True)
    billing_date = Column(Date, nullable=True)
    period_start = Column(Date, nullable=True)
    period_end = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)

    balance_bf = Column(Numeric(14, 2), nullable=True)
    payments_received = Column(Numeric(14, 2), nullable=True)
    charges_for_period = Column(Numeric(14, 2), nullable=True)
    total_payable = Column(Numeric(14, 2), nullable=True)

    # A rough extraction-quality signal, not a true business reconciliation
    # (there's no employee split to reconcile here) — flags if Gemini's
    # itemized line items don't sum close to the stated total, which would
    # suggest a mis-extraction worth reviewing.
    line_items_sum = Column(Numeric(14, 2), nullable=True)
    extraction_discrepancy = Column(Numeric(14, 2), nullable=True)

    extraction_method = Column(String, nullable=False, default="gemini")

    created_at = Column(DateTime(timezone=True), server_default=func.now())