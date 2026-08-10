import enum
import uuid

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum, func

from app.database import Base
from app.types import GUID


class MobileNumberStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"   # no longer in use by anyone (e.g. cancelled)


class MobileNumber(Base):
    """
    A mobile number belongs to exactly one employee at a time, but an
    employee can hold more than one number (confirmed by real data: some
    employees are billed on two numbers under the same EMP No, e.g. a
    primary line plus a project/device line).

    A transfer moves a MobileNumber row's employee_id to a different
    employee — the number itself is never duplicated or deleted.
    """

    __tablename__ = "dialog_mobile_mobile_numbers"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    employee_id = Column(GUID, ForeignKey("dialog_mobile_employees.id"), nullable=False, index=True)

    mobile_no = Column(String, nullable=False, index=True)
    is_primary = Column(Boolean, nullable=False, default=False)
    status = Column(Enum(MobileNumberStatus), nullable=False, default=MobileNumberStatus.active)

    # Some of an employee's numbers are cost-allocated to a specific
    # project (confirmed real cases: "Panitha Bimsara-IPTV Project",
    # "Upul Naulla-Delivery", "Ravindra Dharmasena-NTB Project" — the
    # source sheet encoded this directly in the Name column, which meant
    # the employee's OWN name got silently overwritten by whichever row
    # happened to be read first, since Employee.name is a single shared
    # field, not per-number). This keeps the employee's name clean and
    # consistent, while preserving the per-number project allocation here.
    project_label = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())