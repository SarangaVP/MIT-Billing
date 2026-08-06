import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class MobitelStaticIpRateCreate(BaseModel):
    employee_id: uuid.UUID
    cost: Decimal
    effective_from: date


class MobitelStaticIpRateOut(BaseModel):
    id: uuid.UUID
    employee_id: uuid.UUID
    employee_name: str | None = None
    cost: Decimal
    effective_from: date
    created_at: datetime

    model_config = {"from_attributes": True}