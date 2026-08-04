import enum
import uuid

from sqlalchemy import Column, String, Numeric, Boolean, DateTime, Enum, func
from sqlalchemy.orm import relationship

from app.database import Base
from app.types import GUID


class EmployeeStatus(str, enum.Enum):
    active = "active"
    resigned = "resigned"
    transferred = "transferred"


class Employee(Base):
    __tablename__ = "employees"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    emp_no = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)

    lob = Column(String, nullable=True)
    cadre = Column(String, nullable=True)
    credit_limit = Column(Numeric(12, 2), nullable=True)
    level = Column(String, nullable=True)
    email = Column(String, nullable=True)

    status = Column(Enum(EmployeeStatus), nullable=False, default=EmployeeStatus.active)
    is_deleted = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    mobile_numbers = relationship(
        "MobileNumber",
        backref="employee",
        order_by="MobileNumber.is_primary.desc()",
        cascade="all, delete-orphan",
    )