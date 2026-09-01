import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.dialog_mobile_mobile_number import DialogMobileMobileNumberOut


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


class DialogMobileEmployeeOut(DialogMobileEmployeeBase):
    id: uuid.UUID
    is_deleted: bool
    is_general_line: bool
    created_at: datetime
    updated_at: datetime
    mobile_numbers: list[DialogMobileMobileNumberOut] = []

    model_config = {"from_attributes": True}