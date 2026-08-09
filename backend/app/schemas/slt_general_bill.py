import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class SltGeneralAccountOut(BaseModel):
    id: uuid.UUID
    account_no: str
    label: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SltGeneralAccountUpdate(BaseModel):
    label: str


class SltGeneralBillPeriodOut(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    account_no: str | None = None
    account_label: str | None = None
    label: str
    invoice_no: str | None
    billing_date: date | None
    period_start: date | None
    period_end: date | None
    due_date: date | None
    balance_bf: Decimal | None
    payments_received: Decimal | None
    charges_for_period: Decimal | None
    total_payable: Decimal | None
    line_items_sum: Decimal | None
    extraction_discrepancy: Decimal | None
    extraction_method: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SltGeneralBillLineItemOut(BaseModel):
    id: uuid.UUID
    description: str
    amount: Decimal

    model_config = {"from_attributes": True}


class SltGeneralImportOneResult(BaseModel):
    filename: str
    success: bool
    bill_period_id: uuid.UUID | None = None
    account_no: str | None = None
    account_label: str | None = None
    charges_for_period: Decimal | None = None
    line_items_sum: Decimal | None = None
    error: str | None = None


class SltGeneralImportBatchResult(BaseModel):
    results: list[SltGeneralImportOneResult]