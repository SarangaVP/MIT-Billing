import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class DialogDataBillPeriodOut(BaseModel):
    id: uuid.UUID
    label: str
    invoice_no: str | None
    mobile_no: str | None
    invoice_date: date | None
    period_start: date | None
    period_end: date | None
    data_charge: Decimal | None
    govt_taxes: Decimal | None
    vat: Decimal | None
    total: Decimal | None
    net: Decimal | None
    users_count: int | None
    per_user_cost: Decimal | None
    reconciled: bool
    reconciliation_discrepancy: Decimal | None
    extraction_method: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DialogDataImportResult(BaseModel):
    bill_period_id: uuid.UUID
    line_items_created: int
    users_count: int
    net: Decimal
    per_user_cost: Decimal
    parsed_total: Decimal
    reconciled: bool
    reconciliation_discrepancy: Decimal
    extraction_method: str
    unmatched_in_bill_sheet: list[str] = []


class DialogDataProjectCostUpdateInput(BaseModel):
    is_project_cost: bool
    project_cost_amount: Decimal | None = None


class DialogDataBillLineItemOut(BaseModel):
    id: uuid.UUID
    connection_id: uuid.UUID
    emp_no: str | None
    name: str | None
    team: str | None
    lob_code: str | None = None
    connection_no: str | None
    cost: Decimal
    is_project_cost: bool = False
    project_cost_amount: Decimal | None = None

    allocation_gb: str | None = None
    usage_gb: str | None = None
    remaining_gb: str | None = None
    pay_go_status: str | None = None
    bill_cycle: str | None = None

    model_config = {"from_attributes": True}