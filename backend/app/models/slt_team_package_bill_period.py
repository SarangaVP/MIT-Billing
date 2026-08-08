import uuid

from sqlalchemy import Column, String, Date, Numeric, Integer, Boolean, DateTime, func

from app.database import Base
from app.types import GUID


class SltTeamPackageBillPeriod(Base):
    """
    One imported monthly bill for the SLT team package account
    (004 767 150X, confirmed fixed every month). The per-employee cost
    comes from a FIXED price per package type, captured directly from
    that month's uploaded Summary Excel (no persistent employee roster —
    the Excel is uploaded fresh every month and IS the source of truth).
    Reconciliation checks: sum(that month's package prices) + Cess +
    SSCL + VAT should equal the PDF's stated Total Charges for the
    Period — confirmed exact against a real bill (29,000 + 591.60 +
    757.54 + 5,462.85 = 35,811.99).
    """

    __tablename__ = "slt_team_package_bill_periods"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    label = Column(String, nullable=False)          # e.g. "June 2026"
    account_no = Column(String, nullable=True)
    invoice_no = Column(String, nullable=True)
    billing_date = Column(Date, nullable=True)
    period_start = Column(Date, nullable=True)
    period_end = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)

    balance_bf = Column(Numeric(14, 2), nullable=True)
    payments_received = Column(Numeric(14, 2), nullable=True)
    cess = Column(Numeric(14, 2), nullable=True)
    sscl = Column(Numeric(14, 2), nullable=True)
    vat = Column(Numeric(14, 2), nullable=True)
    charges_for_period = Column(Numeric(14, 2), nullable=True)   # PDF's stated total for the period
    total_payable = Column(Numeric(14, 2), nullable=True)

    users_count = Column(Integer, nullable=True)
    package_sum = Column(Numeric(14, 2), nullable=True)          # sum of that month's package prices

    reconciled = Column(Boolean, nullable=False, default=True)
    reconciliation_discrepancy = Column(Numeric(14, 2), nullable=True)

    extraction_method = Column(String, nullable=False, default="gemini")   # Gemini-only for this module, no fallback

    created_at = Column(DateTime(timezone=True), server_default=func.now())