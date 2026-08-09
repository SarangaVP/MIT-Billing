import uuid
import enum

from sqlalchemy import Column, String, Boolean, DateTime, Enum, ForeignKey, func

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

    created_at = Column(DateTime(timezone=True), server_default=func.now())