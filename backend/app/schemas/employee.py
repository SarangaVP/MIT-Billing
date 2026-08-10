import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.mobile_number import MobileNumberOut


class EmployeeBase(BaseModel):
    emp_no: str = Field(..., examples=["77959", "PC0007"])
    name: str
    lob: str | None = None
    cadre: str | None = None
    credit_limit: Decimal | None = None
    level: str | None = None
    email: str | None = None
    resignation: str | None = None  # free text, e.g. "No" or a date — matches source sheet


class EmployeeCreate(EmployeeBase):
    # Optional: some real employees (typically senior staff) legitimately
    # have no company mobile number at all. Additional numbers, if any,
    # are added afterward via POST /employees/{id}/mobile-numbers.
    mobile_no: str | None = Field(None, examples=["740052313"])


class EmployeeUpdate(BaseModel):
    """All fields optional — only what's sent gets updated (PATCH-style PUT)."""

    emp_no: str | None = None
    name: str | None = None
    lob: str | None = None
    cadre: str | None = None
    credit_limit: Decimal | None = None
    level: str | None = None
    email: str | None = None
    resignation: str | None = None


class EmployeeOut(EmployeeBase):
    id: uuid.UUID
    is_deleted: bool
    is_shared_line: bool
    created_at: datetime
    updated_at: datetime
    mobile_numbers: list[MobileNumberOut] = []

    model_config = {"from_attributes": True}