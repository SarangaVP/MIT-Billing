import uuid
import enum

from sqlalchemy import Column, String, Numeric, Boolean, DateTime, Enum, ForeignKey, func

from app.database import Base
from app.types import GUID


class MobitelConnectionStatus(str, enum.Enum):
    active = "active"      # currently billed, included in the next split
    inactive = "inactive"   # kept for history, excluded from billing


class MobitelConnection(Base):
    """
    One row per Mobitel data bucket SIM. An employee can hold more than
    one (schema now supports it, even though no such case exists yet in
    real data — see MobitelEmployee's docstring for why this was
    rebuilt). Only "active" connections belonging to a non-pool,
    non-deleted employee are split across when a bill is imported.
    """

    __tablename__ = "mobitel_connections"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    employee_id = Column(GUID, ForeignKey("mobitel_employees.id"), nullable=False, index=True)

    mobile_no = Column(String, unique=True, nullable=False, index=True)
    status = Column(Enum(MobitelConnectionStatus), nullable=False, default=MobitelConnectionStatus.active)
    is_deleted = Column(Boolean, nullable=False, default=False)

    # Some rows in the Master sheet encode a per-connection project
    # allocation directly in the Name column (e.g. "SLA-IPTV Project"),
    # same convention as Dialog Mobile's project_label on MobileNumber.
    # When set AND a Portal file is uploaded with this month's bill,
    # the connection's project cost is calculated automatically instead
    # of the equal per-user split — see mobitel_bill_service.py.
    project_label = Column(String, nullable=True)

    # A persistent, per-connection static IP cost that should be applied
    # automatically on EVERY future bill import — used for connections
    # with a real, unchanging static IP charge every month (confirmed
    # real case: 711434957 always carries Rs. 1500), so it no longer
    # needs to be manually re-entered via "Manage static IP" each time.
    # Still fully editable per bill period afterward if a specific month
    # genuinely needs a different value.
    default_static_ip_cost = Column(Numeric(12, 2), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())