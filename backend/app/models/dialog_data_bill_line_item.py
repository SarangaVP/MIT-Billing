import uuid

from sqlalchemy import Column, String, Numeric, Boolean, DateTime, ForeignKey, func

from app.database import Base
from app.types import GUID


class DialogDataBillLineItem(Base):
    """
    One row per active CONNECTION per bill period (not per employee — an
    employee with 2 connections gets 2 line items, confirmed against real
    data). Computed by splitting Net evenly across active connections,
    NOT parsed from the bill file.
    """

    __tablename__ = "dialog_data_bill_line_items"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    bill_period_id = Column(GUID, ForeignKey("dialog_data_bill_periods.id"), nullable=False, index=True)
    connection_id = Column(GUID, ForeignKey("dialog_data_connections.id"), nullable=False, index=True)

    cost = Column(Numeric(12, 2), nullable=False)

    # Frozen copy of who this connection was billed to AT IMPORT TIME —
    # deliberately NOT looked up live via connection -> employee at read
    # time. A connection's employee_id can be reassigned later (an EMP No
    # collision resolved via the Master sheet sync, an employee genuinely
    # transferring a number to someone else) — without this snapshot, that
    # reassignment would silently rewrite who every past bill appears to
    # have been billed to, which is wrong for a billing history. These 4
    # fields are the source of truth for display from the moment the bill
    # is created; connection_no is included too so a bill still displays
    # correctly even if a connection is later soft-deleted.
    connection_no_snapshot = Column(String, nullable=True)
    emp_no_snapshot = Column(String, nullable=True)
    name_snapshot = Column(String, nullable=True)
    team_snapshot = Column(String, nullable=True)
    lob_code_snapshot = Column(String, nullable=True)

    # A manually-set project cost, used when someone's real charge for the
    # month is a specific known amount rather than an equal share of the
    # bucket — same concept and behavior as Mobitel's project cost. When
    # True, cost = project_cost_amount for this row, and this row is
    # excluded from BOTH the shared pool (Net) and the headcount (Users)
    # for everyone else's equal split.
    is_project_cost = Column(Boolean, nullable=False, default=False)
    project_cost_amount = Column(Numeric(12, 2), nullable=True)

    # Only populated when the "Bill" sheet was uploaded alongside the PDF —
    # stored as raw strings, since real data includes non-numeric values
    # like "UNLIMITED" and "NaN" that would break a numeric column.
    allocation_gb = Column(String, nullable=True)
    usage_gb = Column(String, nullable=True)
    remaining_gb = Column(String, nullable=True)
    pay_go_status = Column(String, nullable=True)
    bill_cycle = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())