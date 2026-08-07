import uuid

from sqlalchemy import Column, String, Boolean, DateTime, func
from sqlalchemy.orm import relationship

from app.database import Base
from app.types import GUID


class DialogDataEmployee(Base):
    """
    One row per employee. Connections live in a SEPARATE table
    (dialog_data_connections) — confirmed against the real Master sheet
    that an employee can hold more than one connection (e.g. Indusarani
    Silva has 2, each billed separately at the full per-connection rate).
    This mirrors Dialog Mobile's Employee/MobileNumber split, NOT
    Mobitel's simpler 1:1 model.

    Seeded once from the Dialog Data Bucket export's "Master sheet" — NOT
    re-synced monthly.
    """

    __tablename__ = "dialog_data_employees"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    emp_no = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    team = Column(String, nullable=True)   # matches "Team"/"LOB" text column in the source sheet

    # Numeric LOB code, e.g. "32" for BFSI, "76" for Corporate. Sourced
    # from the export's separate "LOB" sheet (an org-chart/HR export), NOT
    # the Master sheet — joined by EMP No. Confirmed real coverage: ~95%
    # of Master sheet employees have a match; the rest (people without a
    # matching HR record in that sheet) stay NULL. Stored as a string —
    # matches the pattern used for Mobitel's lob_code, for consistency,
    # even though no leading-zero codes were seen in this specific file.
    lob_code = Column(String, nullable=True)

    is_deleted = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    connections = relationship(
        "DialogDataConnection",
        backref="employee",
        cascade="all, delete-orphan",
    )