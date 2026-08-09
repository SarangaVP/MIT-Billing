import uuid

from sqlalchemy import Column, String, Boolean, DateTime, func
from sqlalchemy.orm import relationship

from app.database import Base
from app.types import GUID


class MobitelEmployee(Base):
    """
    One row per employee holding one or more Mobitel data bucket SIMs.
    Connections live in a SEPARATE table (mobitel_connections) — this
    mirrors Dialog Data Bucket's Employee/Connection split, NOT the
    original 1:1 design. Rebuilt this way after confirming the original
    design (mobile_no directly on the employee row) had no way to
    represent a person holding more than one SIM: testing the actual
    seed script against a synthetic case showed it silently dropped a
    second mobile number with zero warning. No such case exists in the
    real June/July data (confirmed by checking), but the schema now
    supports it correctly if it ever does.

    "Pool" (unassigned SIM, held by no real person) is now represented
    as is_pool=True on a synthetic employee record, same naming pattern
    as before ("POOL-<mobile_no>" as emp_no) — but underneath, even a
    Pool employee now has a real Connection row. Pool employees are
    always excluded from billing regardless of their connection's status.
    """

    __tablename__ = "mobitel_employees"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    emp_no = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    lob = Column(String, nullable=True)
    lob_code = Column(String, nullable=True)

    is_pool = Column(Boolean, nullable=False, default=False)
    is_deleted = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    connections = relationship(
        "MobitelConnection",
        primaryjoin="and_(MobitelEmployee.id==MobitelConnection.employee_id, MobitelConnection.is_deleted==False)",
        backref="employee",
    )