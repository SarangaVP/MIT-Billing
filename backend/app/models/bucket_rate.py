import uuid

from sqlalchemy import Column, Numeric, DateTime, func

from app.database import Base
from app.types import GUID


class BucketRate(Base):
    """
    The flat monthly plan cost per line (confirmed from the source Excel:
    a constant, e.g. 590.39 cost / 90.06 VAT, applied to ~99% of active
    lines) — NOT extracted from any bill, since it's your company's fixed
    package rate with Dialog, not a usage-based charge.

    Modeled as a table (not a single config value) so a future rate change
    doesn't rewrite history — each bill period looks up whichever rate was
    effective on its date.
    """

    __tablename__ = "dialog_mobile_bucket_rates"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    cost = Column(Numeric(12, 2), nullable=False)
    vat = Column(Numeric(12, 2), nullable=False)
    effective_from = Column(DateTime(timezone=True), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())