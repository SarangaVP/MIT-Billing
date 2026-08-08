import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class SltTeamPackageBillPeriodOut(BaseModel):
    id: uuid.UUID
    label: str
    account_no: str | None
    invoice_no: str | None
    billing_date: date | None
    period_start: date | None
    period_end: date | None
    due_date: date | None
    balance_bf: Decimal | None
    payments_received: Decimal | None
    cess: Decimal | None
    sscl: Decimal | None
    vat: Decimal | None
    charges_for_period: Decimal | None
    total_payable: Decimal | None
    users_count: int | None
    package_sum: Decimal | None
    reconciled: bool
    reconciliation_discrepancy: Decimal | None
    extraction_method: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SltTeamPackageImportResult(BaseModel):
    bill_period_id: uuid.UUID
    line_items_created: int
    users_count: int
    package_sum: Decimal
    charges_for_period: Decimal
    computed_total: Decimal   # package_sum + cess + sscl + vat
    reconciled: bool
    reconciliation_discrepancy: Decimal


class SltTeamPackageBillLineItemOut(BaseModel):
    id: uuid.UUID
    name: str
    team: str | None
    lob_code: str | None
    package_name: str
    package_price: Decimal

    model_config = {"from_attributes": True}