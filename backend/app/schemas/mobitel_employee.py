import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.mobitel_employee import MobitelEmployeeStatus


class MobitelEmployeeBase(BaseModel):
    emp_no: str
    name: str
    mobile_no: str
    lob: str | None = None


class MobitelEmployeeCreate(MobitelEmployeeBase):
    pass


class MobitelEmployeeUpdate(BaseModel):
    emp_no: str | None = None
    name: str | None = None
    mobile_no: str | None = None
    lob: str | None = None
    status: MobitelEmployeeStatus | None = None


class MobitelEmployeeOut(MobitelEmployeeBase):
    id: uuid.UUID
    status: MobitelEmployeeStatus
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}