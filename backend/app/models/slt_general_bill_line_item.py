import uuid

from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, func

from app.database import Base
from app.types import GUID


class SltGeneralBillLineItem(Base):
    """
    One row per itemized charge line (e.g. "SLT BroadBand Service Any
    Xtreme [Rental]" -> 26,250.00). Deliberately flexible — confirmed
    real bills have wildly different charge shapes (broadband, static
    IP, fiber, voice VAS, PeoTV, business internet), so a free-form
    description+amount pair is more robust than fixed columns.
    """

    __tablename__ = "slt_general_bill_line_items"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    bill_period_id = Column(GUID, ForeignKey("slt_general_bill_periods.id"), nullable=False, index=True)

    description = Column(String, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())