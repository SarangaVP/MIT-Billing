import uuid

from sqlalchemy import Column, Numeric, DateTime, ForeignKey, func

from app.database import Base
from app.types import GUID


class MobitelBillLineItem(Base):
    """
    One row per active employee per bill period. Unlike Dialog, these are
    NOT parsed from the bill file — computed by splitting that month's Net
    cost evenly across whoever was active at import time.
    """

    __tablename__ = "mobitel_bill_line_items"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    bill_period_id = Column(GUID, ForeignKey("mobitel_bill_periods.id"), nullable=False, index=True)
    employee_id = Column(GUID, ForeignKey("mobitel_employees.id"), nullable=False, index=True)

    data_cost = Column(Numeric(12, 2), nullable=False)
    static_ip_cost = Column(Numeric(12, 2), nullable=False, default=0)
    total = Column(Numeric(12, 2), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())