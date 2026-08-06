import uuid

from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, func

from app.database import Base
from app.types import GUID


class DialogDataBillLineItem(Base):
    """
    One row per active CONNECTION per bill period (not per employee — an
    employee with 2 connections gets 2 line items, confirmed against real
    data). Computed by splitting Net evenly across active connections,
    NOT parsed from the bill file.
    """

    __tablename__ = "dialog_data_bill_line_items"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    bill_period_id = Column(GUID, ForeignKey("dialog_data_bill_periods.id"), nullable=False, index=True)
    connection_id = Column(GUID, ForeignKey("dialog_data_connections.id"), nullable=False, index=True)

    cost = Column(Numeric(12, 2), nullable=False)

    # Only populated when the "Bill" sheet was uploaded alongside the PDF —
    # stored as raw strings, since real data includes non-numeric values
    # like "UNLIMITED" and "NaN" that would break a numeric column.
    allocation_gb = Column(String, nullable=True)
    usage_gb = Column(String, nullable=True)
    remaining_gb = Column(String, nullable=True)
    pay_go_status = Column(String, nullable=True)
    bill_cycle = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())