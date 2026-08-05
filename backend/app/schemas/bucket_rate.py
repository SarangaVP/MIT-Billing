import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class BucketRateCreate(BaseModel):
    cost: Decimal
    vat: Decimal
    effective_from: date


class BucketRateOut(BaseModel):
    id: uuid.UUID
    cost: Decimal
    vat: Decimal
    effective_from: date
    created_at: datetime

    model_config = {"from_attributes": True}