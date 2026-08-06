import uuid

from sqlalchemy import Column, String, DateTime, ForeignKey, func

from app.database import Base
from app.types import GUID, JSONVariant


class EmployeeAuditLog(Base):
    """
    Every create/update/resign/transfer/delete on an employee writes a row
    here. This matters for a finance tool: if a credit limit or mobile-no
    mapping changes and a bill allocation looks wrong later, you need to
    know who changed what and when — not just the current state.
    """

    __tablename__ = "dialog_mobile_employee_audit_log"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    employee_id = Column(GUID, ForeignKey("dialog_mobile_employees.id"), nullable=False, index=True)

    change_type = Column(String, nullable=False)  # created | updated | resigned | transferred | deleted
    changed_by = Column(String, nullable=True)     # left nullable until auth is added
    old_values = Column(JSONVariant, nullable=True)
    new_values = Column(JSONVariant, nullable=True)

    changed_at = Column(DateTime(timezone=True), server_default=func.now())