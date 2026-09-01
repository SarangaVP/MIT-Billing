import re
import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, field_validator

from app.models.mobitel_connection import MobitelConnectionStatus


def _normalize_whitespace(value: str | None) -> str | None:
    """
    Confirmed real bug this prevents: the Master sheet sync already
    normalizes whitespace on import (see mobitel_sheet_sync.py's clean()),
    but that's a completely separate code path from this API — someone
    manually editing an employee through the UI could easily reintroduce
    a trailing or doubled-up space (e.g. "Managed Services " or
    "Managed  Services") that silently breaks this module's own Team
    Cost grouping, which keys directly off the raw team/lob string.
    Trimming the edges and collapsing any run of internal whitespace
    down to a single space here closes that gap for every caller of this
    API, not just the sheet upload path.
    """
    if value is None:
        return None
    value = re.sub(r"\s+", " ", value).strip()
    return value or None


class MobitelConnectionOut(BaseModel):
    id: uuid.UUID
    mobile_no: str
    status: MobitelConnectionStatus
    default_static_ip_cost: Decimal | None = None

    model_config = {"from_attributes": True}


class MobitelConnectionCreate(BaseModel):
    mobile_no: str

    @field_validator("mobile_no", mode="before")
    @classmethod
    def _normalize(cls, value):
        return _normalize_whitespace(value)


class MobitelConnectionDefaultStaticIpInput(BaseModel):
    default_static_ip_cost: Decimal | None = None  # null clears it


class MobitelEmployeeBase(BaseModel):
    emp_no: str
    name: str
    lob: str | None = None
    lob_code: str | None = None

    @field_validator("emp_no", "name", "lob", "lob_code", mode="before")
    @classmethod
    def _normalize(cls, value):
        return _normalize_whitespace(value)


class MobitelEmployeeCreate(MobitelEmployeeBase):
    mobile_no: str | None = None   # optional initial connection, like Dialog Mobile/Dialog Data

    @field_validator("mobile_no", mode="before")
    @classmethod
    def _normalize_mobile_no(cls, value):
        return _normalize_whitespace(value)


class MobitelEmployeeUpdate(BaseModel):
    emp_no: str | None = None
    name: str | None = None
    lob: str | None = None
    lob_code: str | None = None

    @field_validator("emp_no", "name", "lob", "lob_code", mode="before")
    @classmethod
    def _normalize(cls, value):
        return _normalize_whitespace(value)


class MobitelEmployeeOut(MobitelEmployeeBase):
    id: uuid.UUID
    is_pool: bool
    is_deleted: bool
    connections: list[MobitelConnectionOut] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}