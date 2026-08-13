import uuid

from sqlalchemy import Column, String, Numeric, Boolean, DateTime, func
from sqlalchemy.orm import relationship

from app.database import Base
from app.types import GUID


class Employee(Base):
    __tablename__ = "dialog_mobile_employees"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    # EMP No is text, not int — some real values are codes like "PC0007"
    emp_no = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)

    # Mobile numbers live in their own table (app.models.mobile_number) —
    # an employee can hold more than one number at a time, or none at all.

    lob = Column(String, nullable=True)
    cadre = Column(String, nullable=True)
    credit_limit = Column(Numeric(12, 2), nullable=True)
    level = Column(String, nullable=True)
    email = Column(String, nullable=True)

    # Plain text, matching the source sheet exactly: usually "No", sometimes
    # a resignation date (formats vary in the source data). Not modeled as a
    # structured status/date — edited directly, same as every other field.
    resignation = Column(String, nullable=True)

    # True for a synthetic entry representing a pooled "General"
    # line (e.g. a security post phone, a driver's phone) that has no real
    # named employee behind it — the source sheet marks these with the
    # literal text "General" in the EMP No column, not a real EMP No.
    # Confirmed 5 real cases: Security 1/3/4, Driver Perera, Data bucket.
    is_general_line = Column(Boolean, nullable=False, default=False)

    is_deleted = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    mobile_numbers = relationship(
        "MobileNumber",
        backref="employee",
        order_by="MobileNumber.is_primary.desc()",
        cascade="all, delete-orphan",
    )