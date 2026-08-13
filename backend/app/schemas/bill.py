import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class BillPeriodOut(BaseModel):
    id: uuid.UUID
    label: str
    corporate_code: str | None
    bill_period_start: date | None
    bill_period_end: date | None
    invoice_date: date | None
    stated_total_charges_for_bill_period: Decimal | None
    stated_total_due_amount: Decimal | None
    source_format: str
    reconciled: bool
    reconciliation_discrepancy: Decimal | None
    bucket_cost_override: Decimal | None
    bucket_vat_override: Decimal | None
    created_at: datetime

    model_config = {"from_attributes": True}


class BucketRateOverrideInput(BaseModel):
    # Both null clears the override, reverting this bill period back to
    # whatever rate is active in the standard rate table.
    bucket_cost_override: Decimal | None = None
    bucket_vat_override: Decimal | None = None


class ImportResult(BaseModel):
    bill_period_id: uuid.UUID
    line_items_imported: int
    parsed_total_charges_for_bill_period: Decimal
    stated_total_charges_for_bill_period: Decimal | None
    reconciled: bool
    reconciliation_discrepancy: Decimal | None
    source_format: str


class ApprovalOverrideInput(BaseModel):
    approval_override: str | None  # e.g. "Manager approved", or null to clear it


class BucketExclusionInput(BaseModel):
    is_bucket_excluded: bool


class BillSummaryRow(BaseModel):
    """
    Mirrors the source Excel 'Summary' tab, as closely as the source file
    allows. Everything here is either taken straight from the bill or
    computed from a documented rule — nothing is guessed.
    """

    bill_line_item_id: uuid.UUID
    mobile_no: str

    emp_no: str | None
    name: str | None
    lob: str | None
    cadre: str | None
    credit_limit: Decimal | None
    level: str | None
    email: str | None
    project_label: str | None

    total_usage_charges: Decimal
    # Only populated when the bill was imported from the .xls source —
    # None for PDF-sourced imports, which only give the combined total above.
    voice_rental: Decimal | None
    voice_usage: Decimal | None
    sms: Decimal | None
    data_rental: Decimal | None
    data_usage: Decimal | None

    idd: Decimal
    roaming: Decimal
    vas: Decimal
    charges_for_bill_period: Decimal
    vat: Decimal
    add_to_bill_charges: Decimal

    net_amount: Decimal
    bucket_cost: Decimal
    bucket_vat: Decimal
    bucket_nett: Decimal
    total: Decimal
    salary_deduction: Decimal
    need_approval: str
    is_overridden: bool
    is_general_line: bool
    is_bucket_excluded: bool