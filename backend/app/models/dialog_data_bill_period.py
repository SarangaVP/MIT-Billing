import uuid

from sqlalchemy import Column, String, Date, Numeric, Integer, Boolean, DateTime, func

from app.database import Base
from app.types import GUID


class DialogDataBillPeriod(Base):
    """
    One imported monthly Dialog Data Bucket bill. Like Mobitel, the PDF is
    a single master-account total with NO per-employee breakdown — line
    items are computed by the app itself, splitting Net across active
    connections, not parsed from the file.
    """

    __tablename__ = "dialog_data_bill_periods"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    label = Column(String, nullable=False)          # e.g. "July 2026"
    invoice_no = Column(String, nullable=True)
    mobile_no = Column(String, nullable=True)        # the master account's own number, e.g. 765153653
    invoice_date = Column(Date, nullable=True)
    period_start = Column(Date, nullable=True)
    period_end = Column(Date, nullable=True)

    data_charge = Column(Numeric(14, 2), nullable=True)
    govt_taxes = Column(Numeric(14, 2), nullable=True)
    vat = Column(Numeric(14, 2), nullable=True)
    total = Column(Numeric(14, 2), nullable=True)         # "Total Charges for Bill Period"
    net = Column(Numeric(14, 2), nullable=True)            # total - vat, computed

    users_count = Column(Integer, nullable=True)
    per_user_cost = Column(Numeric(12, 4), nullable=True)

    reconciled = Column(Boolean, nullable=False, default=True)
    reconciliation_discrepancy = Column(Numeric(14, 2), nullable=True)

    # "gemini" (primary) or "regex_fallback" — same transparency as Mobitel
    extraction_method = Column(String, nullable=False, default="regex_fallback")

    created_at = Column(DateTime(timezone=True), server_default=func.now())