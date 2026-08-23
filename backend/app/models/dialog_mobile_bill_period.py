import uuid

from sqlalchemy import Column, String, Date, Numeric, Boolean, DateTime, func

from app.database import Base
from app.types import GUID


class DialogMobileBillPeriod(Base):
    """One imported monthly bill (one file import = one row here)."""

    __tablename__ = "dialog_mobile_bill_periods"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    label = Column(String, nullable=False)                 # e.g. "July 2026"
    corporate_code = Column(String, nullable=True)
    bill_period_start = Column(Date, nullable=True)
    bill_period_end = Column(Date, nullable=True)
    invoice_date = Column(Date, nullable=True)

    stated_total_charges_for_bill_period = Column(Numeric(14, 2), nullable=True)
    stated_total_due_amount = Column(Numeric(14, 2), nullable=True)

    # "pdf" or "xls" — which file this import actually came from.
    source_format = Column(String, nullable=False, default="pdf")

    # PDF imports are reconciled strictly (must match to the cent, or the
    # import is rejected outright). .xls imports are relaxed — some months
    # it structurally omits dormant/zero-activity accounts, so a small
    # mismatch is expected and allowed, but always recorded here rather
    # than hidden, so it stays visible for review.
    reconciled = Column(Boolean, nullable=False, default=True)
    reconciliation_discrepancy = Column(Numeric(14, 2), nullable=True)

    # Optional per-bill-period override of the bucket cost/VAT — set via
    # "Set bucket rate" on the Bills page for that specific month. There is
    # no fallback/standard rate anymore: if both are NULL, bucket cost and
    # VAT are simply zero for every line item in this bill period until an
    # override is set.
    bucket_cost_override = Column(Numeric(12, 2), nullable=True)
    bucket_vat_override = Column(Numeric(12, 2), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())