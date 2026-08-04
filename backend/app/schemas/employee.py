import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.employee import EmployeeStatus
from app.schemas.mobile_number import MobileNumberOut


class EmployeeBase(BaseModel):
    emp_no: str = Field(..., examples=["77959", "PC0007"])
    name: str
    lob: str | None = None
    cadre: str | None = None
    credit_limit: Decimal | None = None
    level: str | None = None
    email: str | None = None


class EmployeeCreate(EmployeeBase):
    mobile_no: str | None = Field(None, examples=["740052313"])


class EmployeeUpdate(BaseModel):
    emp_no: str | None = None
    name: str | None = None
    lob: str | None = None
    cadre: str | None = None
    credit_limit: Decimal | None = None
    level: str | None = None
    email: str | None = None


class EmployeeOut(EmployeeBase):
    id: uuid.UUID
    status: EmployeeStatus
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    mobile_numbers: list[MobileNumberOut] = []

    model_config = {"from_attributes": True}


class ResignRequest(BaseModel):
    effective_date: datetime
    notes: str | None = None


class TransferRequest(BaseModel):
    mobile_no: str = Field(..., description="Which of the employee's numbers is being transferred")
    new_employee_id: uuid.UUID
    effective_date: datetime
    notes: str | None = None