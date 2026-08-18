import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.mobitel_connection import MobitelConnectionStatus


class MobitelConnectionOut(BaseModel):
    id: uuid.UUID
    mobile_no: str
    status: MobitelConnectionStatus
    default_static_ip_cost: Decimal | None = None

    model_config = {"from_attributes": True}


class MobitelConnectionCreate(BaseModel):
    mobile_no: str


class MobitelConnectionDefaultStaticIpInput(BaseModel):
    default_static_ip_cost: Decimal | None = None  # null clears it


class MobitelEmployeeBase(BaseModel):
    emp_no: str
    name: str
    lob: str | None = None
    lob_code: str | None = None


class MobitelEmployeeCreate(MobitelEmployeeBase):
    mobile_no: str | None = None   # optional initial connection, like Dialog Mobile/Dialog Data


class MobitelEmployeeUpdate(BaseModel):
    emp_no: str | None = None
    name: str | None = None
    lob: str | None = None
    lob_code: str | None = None


class MobitelEmployeeOut(MobitelEmployeeBase):
    id: uuid.UUID
    is_pool: bool
    is_deleted: bool
    connections: list[MobitelConnectionOut] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}