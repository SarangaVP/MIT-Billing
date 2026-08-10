import uuid

from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, func

from app.database import Base
from app.types import GUID


class MobitelBillLineItem(Base):
    """
    One row per active CONNECTION per bill period (not per employee — an
    employee with 2+ connections would get 2+ line items, one per
    connection, same pattern as Dialog Data Bucket). Computed by
    splitting Net evenly across active connections, NOT parsed from the
    bill file.
    """

    __tablename__ = "mobitel_bill_line_items"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    bill_period_id = Column(GUID, ForeignKey("mobitel_bill_periods.id"), nullable=False, index=True)
    connection_id = Column(GUID, ForeignKey("mobitel_connections.id"), nullable=False, index=True)

    data_cost = Column(Numeric(12, 2), nullable=False)
    static_ip_cost = Column(Numeric(12, 2), nullable=False, default=0)
    total = Column(Numeric(12, 2), nullable=False)

    # Only populated when a "Portal" sheet was provided alongside the PDF at
    # import time — a monthly per-SIM usage snapshot, matched by mobile
    # number. NULL for any bill imported without a Portal file.
    imsi_number = Column(String, nullable=True)
    data_volume_mb = Column(Numeric(14, 2), nullable=True)
    available_data_volume_mb = Column(Numeric(14, 2), nullable=True)
    utilized_data_volume_mb = Column(Numeric(14, 2), nullable=True)
    daily_limit_mb = Column(Numeric(14, 2), nullable=True)
    utilized_daily_limit_mb = Column(Numeric(14, 2), nullable=True)
    member_status = Column(String, nullable=True)
    top_up_mb = Column(Numeric(14, 2), nullable=True)
    utilized_topup_mb = Column(Numeric(14, 2), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())