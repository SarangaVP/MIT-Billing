import enum
import uuid

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum, func

from app.database import Base
from app.types import GUID


class MobileNumberStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"


class MobileNumber(Base):
    __tablename__ = "mobile_numbers"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    employee_id = Column(GUID, ForeignKey("employees.id"), nullable=False, index=True)

    mobile_no = Column(String, nullable=False, index=True)
    is_primary = Column(Boolean, nullable=False, default=False)
    status = Column(Enum(MobileNumberStatus), nullable=False, default=MobileNumberStatus.active)

    created_at = Column(DateTime(timezone=True), server_default=func.now())