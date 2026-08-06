import uuid

from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, func

from app.database import Base
from app.types import GUID


class BillLineItem(Base):
    """
    One row per mobile number per bill period, parsed directly from the
    PDF's page-2 Summary table. Deliberately does NOT store a Voice/SMS/Data
    breakdown — the summary table only gives a combined 'total_usage_charges'
    figure; splitting it further would require the PDF's per-employee detail
    pages, which was scoped out.

    mobile_no is stored as plain text, not a foreign key to mobile_numbers —
    a bill can reference a number no longer active in the employee system
    (e.g. cancelled lines still show a previous-due balance), so the join
    to an employee is done at query time, not enforced at write time.
    """

    __tablename__ = "bill_line_items"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    bill_period_id = Column(GUID, ForeignKey("bill_periods.id"), nullable=False, index=True)

    mobile_no = Column(String, nullable=False, index=True)

    previous_due_amount = Column(Numeric(12, 2), nullable=False, default=0)
    payments = Column(Numeric(12, 2), nullable=False, default=0)
    total_usage_charges = Column(Numeric(12, 2), nullable=False, default=0)
    idd = Column(Numeric(12, 2), nullable=False, default=0)
    roaming = Column(Numeric(12, 2), nullable=False, default=0)
    vas = Column(Numeric(12, 2), nullable=False, default=0)
    discounts = Column(Numeric(12, 2), nullable=False, default=0)
    bill_adjustments_balance_transfers = Column(Numeric(12, 2), nullable=False, default=0)
    commitment_charges = Column(Numeric(12, 2), nullable=False, default=0)
    late_payment_charges = Column(Numeric(12, 2), nullable=False, default=0)
    add_to_bill_charges = Column(Numeric(12, 2), nullable=False, default=0)
    instalment_plans = Column(Numeric(12, 2), nullable=False, default=0)
    govt_taxes = Column(Numeric(12, 2), nullable=False, default=0)
    vat = Column(Numeric(12, 2), nullable=False, default=0)
    charges_for_bill_period = Column(Numeric(12, 2), nullable=False, default=0)
    total_due_amount = Column(Numeric(12, 2), nullable=False, default=0)

    # Only populated when the source file was the .xls export (it breaks
    # these out); a PDF-sourced import leaves them NULL, since the PDF's
    # summary table only gives the combined total_usage_charges figure.
    voice_rental = Column(Numeric(12, 2), nullable=True)
    voice_usage = Column(Numeric(12, 2), nullable=True)
    sms = Column(Numeric(12, 2), nullable=True)
    data_rental = Column(Numeric(12, 2), nullable=True)
    data_usage = Column(Numeric(12, 2), nullable=True)

    # Mirrors the source Excel's manual override behavior: the automatic
    # "OK"/"Need Approval" rule can be overridden with real text like
    # "Manager approved" — persisted here since it's a genuine decision,
    # not something recomputable.
    approval_override = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())