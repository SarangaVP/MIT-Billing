import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.mobile_number import MobileNumberStatus


class MobileNumberOut(BaseModel):
    id: uuid.UUID
    mobile_no: str
    is_primary: bool
    status: MobileNumberStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class MobileNumberCreate(BaseModel):
    mobile_no: str
    is_primary: bool = False