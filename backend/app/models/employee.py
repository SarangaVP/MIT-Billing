import uuid

from sqlalchemy import Column, String, Numeric, Boolean, DateTime, func
from sqlalchemy.orm import relationship

from app.database import Base
from app.types import GUID


class Employee(Base):
    __tablename__ = "dialog_mobile_employees"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    emp_no = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)

    lob = Column(String, nullable=True)
    cadre = Column(String, nullable=True)
    credit_limit = Column(Numeric(12, 2), nullable=True)
    level = Column(String, nullable=True)
    email = Column(String, nullable=True)

    # Plain text, matching the source sheet exactly: usually "No", sometimes
    # a resignation date (formats vary in the source data). Not modeled as a
    # structured status/date — edited directly, same as every other field.
    resignation = Column(String, nullable=True)

    is_deleted = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    mobile_numbers = relationship(
        "MobileNumber",
        backref="employee",
        order_by="MobileNumber.is_primary.desc()",
        cascade="all, delete-orphan",
    )