import uuid
import enum

from sqlalchemy import Column, String, Boolean, DateTime, Enum, func

from app.database import Base
from app.types import GUID


class MobitelEmployeeStatus(str, enum.Enum):
    active = "active"      # currently holds a billed data bucket line
    inactive = "inactive"   # line removed/suspended, but kept for history
    pool = "pool"           # unassigned SIM, not held by any real person — never billed


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
    lob = Column(String, nullable=True)          # team NAME, e.g. "Managed Services"

    # Numeric LOB code, e.g. "81" for "Managed Services". Stored as a
    # string, not int — confirmed real data includes at least one
    # leading-zero code ("05" for Cyber Security), which an int column
    # would silently strip. Only present in newer file exports (first seen
    # July 2026) — older imports leave this NULL.
    lob_code = Column(String, nullable=True)

    # Only "active" employees are included when splitting a month's Net
    # cost. "pool" rows (unassigned SIMs) are imported and shown for
    # visibility, but the bill service always excludes them.
    status = Column(Enum(MobitelEmployeeStatus), nullable=False, default=MobitelEmployeeStatus.active)
    is_deleted = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())