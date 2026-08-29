import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class DialogMobileBillPeriodOut(BaseModel):
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
    data_bucket_mobile_no: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DialogMobileBucketRateOverrideInput(BaseModel):
    # Both null clears the override, reverting this bill period back to
    # whatever rate is active in the standard rate table. Only used as a
    # fallback when no data_bucket_mobile_no has been selected — see
    # DialogMobileDataBucketSelectionInput below, which is the normal path now.
    bucket_cost_override: Decimal | None = None
    bucket_vat_override: Decimal | None = None


class DialogMobileDataBucketSelectionInput(BaseModel):
    # The mobile number (must belong to a line item already in THIS bill
    # period) whose own Charges for Bill Period / VAT become the shared
    # pool that everyone else's bucket cost/VAT is automatically split
    # from. Null clears the selection, reverting to the manual
    # bucket_cost_override/bucket_vat_override behavior for this month.
    data_bucket_mobile_no: str | None = None


class DialogMobileImportResult(BaseModel):
    bill_period_id: uuid.UUID
    line_items_imported: int
    parsed_total_charges_for_bill_period: Decimal
    stated_total_charges_for_bill_period: Decimal | None
    reconciled: bool
    reconciliation_discrepancy: Decimal | None
    source_format: str


class DialogMobileApprovalOverrideInput(BaseModel):
    approval_override: str | None  # e.g. "Manager approved", or null to clear it


class DialogMobileSalaryDeductionOverrideInput(BaseModel):
    # Null clears the override, reverting to the computed value
    # (VAS + Add To Bill Charges + excess over Credit Limit, if any).
    salary_deduction_override: Decimal | None = None


class DialogMobileBucketExclusionInput(BaseModel):
    is_bucket_excluded: bool


class DialogMobileLineItemChargeUpdateInput(BaseModel):
    """
    Manual correction to a line item's raw charge figures for THIS bill
    period — used via "Manage data bucket" for cases where a connection's
    real billed amount needs a manual fix (e.g. a shared/General line's
    genuine usage charge that should read differently than what the bill
    parsed). Every field is required, since this replaces the full set
    that feeds net_amount/total together.
    """
    total_usage_charges: Decimal
    idd: Decimal
    roaming: Decimal
    charges_for_bill_period: Decimal
    vat: Decimal
    vas: Decimal
    add_to_bill_charges: Decimal


class DialogMobileBillSummaryRow(BaseModel):
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
    late_payment_charges: Decimal

    net_amount: Decimal
    bucket_cost: Decimal
    bucket_vat: Decimal
    bucket_nett: Decimal
    total: Decimal
    salary_deduction: Decimal
    is_salary_deduction_overridden: bool
    need_approval: str
    is_overridden: bool
    is_general_line: bool
    is_bucket_excluded: bool
    # True only for the one line item currently selected as this bill
    # period's "data bucket number" — the frontend pulls this row out of
    # the normal table/sum entirely and renders it as its own row after
    # the Total row instead. Its bucket_cost/bucket_vat/bucket_nett are
    # zero here (it's excluded, same as any other excluded connection) —
    # the pool amounts are its own charges_for_bill_period/vat fields.
    is_data_bucket_line: bool

    # Bill-period-level figures, duplicated on every row for convenience
    # (identical across the whole bill period) so the frontend can show a
    # one-line summary without a second request: how many connections are
    # actually splitting the bucket this month, and the resulting
    # per-employee Nett/VAT/Cost breakdown that standard_bucket_cost above
    # is built from.
    eligible_employee_count: int
    standard_bucket_cost: Decimal
    standard_bucket_vat: Decimal
    standard_bucket_nett: Decimal