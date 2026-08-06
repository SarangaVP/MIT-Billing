import uuid
import enum

from sqlalchemy import Column, String, Boolean, DateTime, Enum, func

from app.database import Base
from app.types import GUID


class MobitelEmployeeStatus(str, enum.Enum):
    active = "active"      # currently holds a billed data bucket line
    inactive = "inactive"   # line removed/suspended, but kept for history


class MobitelEmployee(Base):
    """
    One row per employee holding a Mobitel data bucket SIM. Unlike Dialog
    Mobile, an employee here has exactly one mobile number — the Mobitel
    Summary export showed one row per person, no multi-number cases seen.

    Seeded once from the Mobitel portal's "Summary" export (which already
    has EMP No/LOB, unlike the raw "Portal" export) — NOT re-synced monthly.
    Managed afterward the same way as Dialog Mobile employees.
    """

    __tablename__ = "mobitel_employees"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    emp_no = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    mobile_no = Column(String, unique=True, nullable=False, index=True)
    lob = Column(String, nullable=True)

    status = Column(Enum(MobitelEmployeeStatus), nullable=False, default=MobitelEmployeeStatus.active)
    is_deleted = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())