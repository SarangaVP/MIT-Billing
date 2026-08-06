import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.dialog_data_connection import DialogDataConnectionStatus


class DialogDataConnectionOut(BaseModel):
    id: uuid.UUID
    connection_no: str
    status: DialogDataConnectionStatus

    model_config = {"from_attributes": True}


class DialogDataConnectionCreate(BaseModel):
    connection_no: str


class DialogDataEmployeeBase(BaseModel):
    emp_no: str
    name: str
    team: str | None = None


class DialogDataEmployeeCreate(DialogDataEmployeeBase):
    connection_no: str | None = None   # optional initial connection, like Dialog Mobile


class DialogDataEmployeeUpdate(BaseModel):
    emp_no: str | None = None
    name: str | None = None
    team: str | None = None


class DialogDataEmployeeOut(DialogDataEmployeeBase):
    id: uuid.UUID
    is_deleted: bool
    connections: list[DialogDataConnectionOut] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}