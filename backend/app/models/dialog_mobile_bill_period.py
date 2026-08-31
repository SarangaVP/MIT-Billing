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

    # DEPRECATED — kept only so past bill periods that already had a value
    # here retain their historical record; the "Set bucket rate manually"
    # feature that wrote to these was removed. No code reads these columns
    # anymore (see dialog_mobile_bill_service._build_summary_rows): a bill
    # period with no data_bucket_mobile_no selected now simply gets Rs. 0
    # bucket cost/VAT for everyone, with no manual fallback.
    bucket_cost_override = Column(Numeric(12, 2), nullable=True)
    bucket_vat_override = Column(Numeric(12, 2), nullable=True)

    # The mobile number (within THIS bill period's line items) whose own
    # Charges for Bill Period / VAT ARE the shared "data bucket" pool for
    # the month — e.g. the "Data bucket" General line (765155535). When
    # set, the standard bucket cost/VAT for every other eligible line item
    # is derived automatically from this connection's own charges (see
    # dialog_mobile_bill_service._build_summary_rows). NULL means no data
    # bucket number has been picked yet for this month, in which case
    # bucket cost/VAT is simply Rs. 0 for everyone until one is selected.
    data_bucket_mobile_no = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())