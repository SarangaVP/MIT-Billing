import enum
import uuid

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, func

from app.database import Base
from app.types import GUID


class TransitionType(str, enum.Enum):
    resigned = "resigned"
    transferred = "transferred"


class EmployeeTransition(Base):
    """
    Formalizes what the 'Resigned VS Mobile list' and 'Transfers' Excel tabs
    were tracking by hand: a record of what happened to a mobile number when
    an employee left or a number moved to someone else.
    """

    __tablename__ = "employee_transitions"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    employee_id = Column(GUID, ForeignKey("employees.id"), nullable=False, index=True)
    type = Column(Enum(TransitionType), nullable=False)

    old_mobile_no = Column(String, nullable=False)
    # NULL for a plain resignation with no number reassigned yet
    new_employee_id = Column(GUID, ForeignKey("employees.id"), nullable=True)

    effective_date = Column(DateTime(timezone=True), nullable=False)
    notes = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())