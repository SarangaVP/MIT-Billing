import uuid

from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, func

from app.database import Base
from app.types import GUID


class SltTeamPackageBillLineItem(Base):
    """
    One row per employee named in THAT MONTH's uploaded Summary Excel —
    captured directly here as a snapshot (name, team, LOB code, package),
    not via a foreign key to a persistent employee table. The Excel is
    uploaded fresh every month and IS the source of truth for that
    month's allocation, so there's no separate roster to keep in sync
    or reconcile against — each bill period is self-contained.
    """

    __tablename__ = "slt_team_package_bill_line_items"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    bill_period_id = Column(GUID, ForeignKey("slt_team_package_bill_periods.id"), nullable=False, index=True)

    name = Column(String, nullable=False)
    team = Column(String, nullable=True)
    lob_code = Column(String, nullable=True)
    package_name = Column(String, nullable=False)
    package_price = Column(Numeric(12, 2), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())