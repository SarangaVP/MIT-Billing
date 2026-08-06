import uuid
import enum

from sqlalchemy import Column, String, Boolean, DateTime, Enum, ForeignKey, func

from app.database import Base
from app.types import GUID


class DialogDataConnectionStatus(str, enum.Enum):
    active = "active"      # currently billed, included in the next split
    inactive = "inactive"   # kept for history, excluded from billing


class DialogDataConnection(Base):
    """
    One row per Dialog Data Bucket connection (SIM). An employee can hold
    more than one — confirmed against real data (Indusarani Silva has 2,
    each billed separately). Only "active" connections are split across
    when a bill is imported.
    """

    __tablename__ = "dialog_data_connections"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    employee_id = Column(GUID, ForeignKey("dialog_data_employees.id"), nullable=False, index=True)

    connection_no = Column(String, unique=True, nullable=False, index=True)
    status = Column(Enum(DialogDataConnectionStatus), nullable=False, default=DialogDataConnectionStatus.active)
    is_deleted = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())