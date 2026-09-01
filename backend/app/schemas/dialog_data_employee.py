import re
import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator

from app.models.dialog_data_connection import DialogDataConnectionStatus


def _normalize_whitespace(value: str | None) -> str | None:
    """
    Confirmed real bug this prevents: the Master sheet sync already
    normalizes whitespace on import (see dialog_data_sheet_sync.py's
    clean()), but that's a completely separate code path from this API —
    someone manually editing an employee through the UI could easily
    reintroduce a trailing or doubled-up space (e.g. "Cyber Security "
    or "Cyber  Security") that silently breaks this module's own Team
    Cost grouping, which keys directly off the raw team string. Trimming
    the edges and collapsing any run of internal whitespace down to a
    single space here closes that gap for every caller of this API, not
    just the sheet upload path.
    """
    if value is None:
        return None
    value = re.sub(r"\s+", " ", value).strip()
    return value or None


class DialogDataConnectionOut(BaseModel):
    id: uuid.UUID
    connection_no: str
    status: DialogDataConnectionStatus

    model_config = {"from_attributes": True}


class DialogDataConnectionCreate(BaseModel):
    connection_no: str

    @field_validator("connection_no", mode="before")
    @classmethod
    def _normalize(cls, value):
        return _normalize_whitespace(value)


class DialogDataEmployeeBase(BaseModel):
    emp_no: str
    name: str
    team: str | None = None
    lob_code: str | None = None

    @field_validator("emp_no", "name", "team", "lob_code", mode="before")
    @classmethod
    def _normalize(cls, value):
        return _normalize_whitespace(value)


class DialogDataEmployeeCreate(DialogDataEmployeeBase):
    connection_no: str | None = None   # optional initial connection, like Dialog Mobile

    @field_validator("connection_no", mode="before")
    @classmethod
    def _normalize_connection_no(cls, value):
        return _normalize_whitespace(value)


class DialogDataEmployeeUpdate(BaseModel):
    emp_no: str | None = None
    name: str | None = None
    team: str | None = None
    lob_code: str | None = None

    @field_validator("emp_no", "name", "team", "lob_code", mode="before")
    @classmethod
    def _normalize(cls, value):
        return _normalize_whitespace(value)


class DialogDataEmployeeOut(DialogDataEmployeeBase):
    id: uuid.UUID
    is_deleted: bool
    connections: list[DialogDataConnectionOut] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}