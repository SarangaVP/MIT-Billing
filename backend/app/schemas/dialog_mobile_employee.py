import re
import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.schemas.dialog_mobile_mobile_number import DialogMobileMobileNumberOut


def _normalize_whitespace(value: str | None) -> str | None:
    """
    Confirmed real bug this prevents: the Master sheet sync already
    normalizes whitespace on import (see dialog_mobile_sheet_sync.py'
    clean()), but that's a completely separate code path from this API —
    someone manually editing an employee through "Add/Edit employee"
    could easily reintroduce a trailing or doubled-up space (e.g.
    "Fixed Term " or "Managed  Services") that silently breaks exact-
    match comparisons elsewhere (Project Working's Team/Cadre filter,
    Team Cost's grouping key). Trimming the edges and collapsing any run
    of internal whitespace down to a single space here closes that gap
    for every caller of this API, not just the sheet upload path.
    """
    if value is None:
        return None
    value = re.sub(r"\s+", " ", value).strip()
    return value or None


# Every free-text field an employee has — normalized the same way on both
# create and update, so a value typed by hand behaves identically to one
# that came from the Master sheet sync.
_TEXT_FIELDS_TO_NORMALIZE = ("emp_no", "name", "lob", "lob_code", "cadre", "level", "email", "resignation")


class DialogMobileEmployeeBase(BaseModel):
    emp_no: str = Field(..., examples=["77959", "PC0007"])
    name: str
    lob: str | None = None
    lob_code: str | None = None
    cadre: str | None = None
    credit_limit: Decimal | None = None
    level: str | None = None
    email: str | None = None
    resignation: str | None = None  # free text, e.g. "No" or a date — matches source sheet

    @field_validator(*_TEXT_FIELDS_TO_NORMALIZE, mode="before")
    @classmethod
    def _normalize(cls, value):
        return _normalize_whitespace(value)


class DialogMobileEmployeeCreate(DialogMobileEmployeeBase):
    # Optional: some real employees (typically senior staff) legitimately
    # have no company mobile number at all. Additional numbers, if any,
    # are added afterward via POST /dialog-mobile/employees/{id}/mobile-numbers.
    mobile_no: str | None = Field(None, examples=["740052313"])


class DialogMobileEmployeeUpdate(BaseModel):
    """All fields optional — only what's sent gets updated (PATCH-style PUT)."""

    emp_no: str | None = None
    name: str | None = None
    lob: str | None = None
    lob_code: str | None = None
    cadre: str | None = None
    credit_limit: Decimal | None = None
    level: str | None = None
    email: str | None = None
    resignation: str | None = None

    @field_validator(*_TEXT_FIELDS_TO_NORMALIZE, mode="before")
    @classmethod
    def _normalize(cls, value):
        return _normalize_whitespace(value)


class DialogMobileEmployeeOut(DialogMobileEmployeeBase):
    id: uuid.UUID
    is_deleted: bool
    is_general_line: bool
    created_at: datetime
    updated_at: datetime
    mobile_numbers: list[DialogMobileMobileNumberOut] = []

    model_config = {"from_attributes": True}