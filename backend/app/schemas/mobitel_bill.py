import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class MobitelBillPeriodOut(BaseModel):
    id: uuid.UUID
    label: str
    bill_no: str | None
    account_no: str | None
    bill_date: date | None
    due_date: date | None
    period_start: date | None
    period_end: date | None
    arrears: Decimal | None
    bucket_total: Decimal | None
    vat: Decimal | None
    net: Decimal | None
    total_payable: Decimal | None
    users_count: int | None
    per_user_cost: Decimal | None
    reconciled: bool
    reconciliation_discrepancy: Decimal | None
    bucket_total_gb: Decimal
    extraction_method: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MobitelBucketTotalGbUpdateInput(BaseModel):
    bucket_total_gb: Decimal


class MobitelImportResult(BaseModel):
    bill_period_id: uuid.UUID
    line_items_created: int
    users_count: int
    net: Decimal
    per_user_cost: Decimal
    parsed_total: Decimal          # sum of all line items' totals
    reconciled: bool
    reconciliation_discrepancy: Decimal
    extraction_method: str
    unmatched_in_portal_sheet: list[str] = []


class MobitelStaticIpCostUpdateInput(BaseModel):
    cost: Decimal


class MobitelProjectCostUpdateInput(BaseModel):
    is_project_cost: bool
    project_cost_amount: Decimal | None = None


class MobitelBillLineItemOut(BaseModel):
    id: uuid.UUID
    connection_id: uuid.UUID
    emp_no: str | None
    name: str | None
    lob: str | None
    lob_code: str | None = None
    mobile_no: str | None
    data_cost: Decimal
    static_ip_cost: Decimal
    is_project_cost: bool = False
    project_cost_amount: Decimal | None = None
    project_label: str | None = None
    total: Decimal

    # Only populated when a Portal sheet was uploaded alongside the PDF
    imsi_number: str | None = None
    data_volume_mb: Decimal | None = None
    available_data_volume_mb: Decimal | None = None
    utilized_data_volume_mb: Decimal | None = None
    daily_limit_mb: Decimal | None = None
    utilized_daily_limit_mb: Decimal | None = None
    member_status: str | None = None
    top_up_mb: Decimal | None = None
    utilized_topup_mb: Decimal | None = None

    model_config = {"from_attributes": True}