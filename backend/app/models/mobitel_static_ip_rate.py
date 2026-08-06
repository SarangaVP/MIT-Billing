import uuid

from sqlalchemy import Column, Numeric, Date, DateTime, ForeignKey, func

from app.database import Base
from app.types import GUID


class MobitelStaticIpRate(Base):
    """
    A rare, per-employee exception charge (confirmed real data: only 1 of
    121 employees had one, Rs. 1500/month) — not derivable from any file,
    so it's a small manually-maintained settings table, same pattern as
    Dialog's BucketRate, but keyed to a specific employee rather than
    company-wide.
    """

    __tablename__ = "mobitel_static_ip_rates"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    employee_id = Column(GUID, ForeignKey("mobitel_employees.id"), nullable=False, index=True)

    cost = Column(Numeric(12, 2), nullable=False)
    effective_from = Column(Date, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())