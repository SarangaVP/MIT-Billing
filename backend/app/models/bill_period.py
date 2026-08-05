import uuid

from sqlalchemy import Column, String, Date, Numeric, DateTime, func

from app.database import Base
from app.types import GUID


class BillPeriod(Base):
    """One imported monthly bill (one PDF import = one row here)."""

    __tablename__ = "bill_periods"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    label = Column(String, nullable=False)                 # e.g. "July 2026"
    corporate_code = Column(String, nullable=True)
    bill_period_start = Column(Date, nullable=True)
    bill_period_end = Column(Date, nullable=True)
    invoice_date = Column(Date, nullable=True)

    # Stated on the invoice's own cover page — used to reconcile the sum of
    # line items against, so an import that doesn't add up gets caught
    # immediately rather than silently trusted.
    stated_total_charges_for_bill_period = Column(Numeric(14, 2), nullable=True)
    stated_total_due_amount = Column(Numeric(14, 2), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())