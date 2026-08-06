import uuid

from sqlalchemy import Column, String, Date, Numeric, Integer, Boolean, DateTime, func

from app.database import Base
from app.types import GUID


class MobitelBillPeriod(Base):
    """
    One imported monthly Mobitel bill. Unlike Dialog, the PDF has NO
    per-employee breakdown at all — it's a single company-wide total.
    Line items are therefore computed by the app itself at import time
    (splitting Net across whoever is currently active), not parsed.
    """

    __tablename__ = "mobitel_bill_periods"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    label = Column(String, nullable=False)
    bill_no = Column(String, nullable=True)
    account_no = Column(String, nullable=True)
    bill_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)
    period_start = Column(Date, nullable=True)
    period_end = Column(Date, nullable=True)

    arrears = Column(Numeric(14, 2), nullable=True)
    bucket_total = Column(Numeric(14, 2), nullable=True)
    vat = Column(Numeric(14, 2), nullable=True)
    net = Column(Numeric(14, 2), nullable=True)
    total_payable = Column(Numeric(14, 2), nullable=True)

    users_count = Column(Integer, nullable=True)
    per_user_cost = Column(Numeric(12, 4), nullable=True)

    reconciled = Column(Boolean, nullable=False, default=True)
    reconciliation_discrepancy = Column(Numeric(14, 2), nullable=True)

    extraction_method = Column(String, nullable=False, default="regex_fallback")

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    