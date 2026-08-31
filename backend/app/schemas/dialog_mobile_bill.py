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
    data_bucket_mobile_no: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DialogMobileDataBucketSelectionInput(BaseModel):
    # The mobile number (must belong to a line item already in THIS bill
    # period) whose own Charges for Bill Period / VAT become the shared
    # pool that everyone else's bucket cost/VAT is automatically split
    # from. Null clears the selection — with no manual fallback anymore,
    # this simply results in Rs. 0 bucket cost for everyone until a data
    # bucket number is selected again.
    data_bucket_mobile_no: str | None = None


class DialogMobileImportResult(BaseModel):
    bill_period_id: uuid.UUID
    line_items_imported: int
    parsed_total_charges_for_bill_period: Decimal
    stated_total_charges_for_bill_period: Decimal | None
    reconciled: bool
    reconciliation_discrepancy: Decimal | None
    source_format: str
    # Connections whose source file had a value too large to store (e.g. a
    # broken/circular Excel formula in Dialog's own export serializing to
    # something like 76,669,945,315,413.83) — confirmed real, seen on a
    # genuine .xls invoice. The offending field is reset to 0 so the import
    # can still complete and the connection isn't silently dropped from the
    # bill, but this is surfaced here so it can be checked/corrected
    # manually via "Edit line item".
    corrupted_value_warnings: list[str] = []


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
    period — used via "Edit line item" for any connection whose real
    billed amount needs a manual fix (e.g. a shared/General line's genuine
    usage charge that should read differently than what the bill parsed,
    or any other connection's figures). Every field is required, since
    this replaces the full set that feeds net_amount/total/salary
    deduction/Project Working together.
    """
    total_usage_charges: Decimal
    idd: Decimal
    roaming: Decimal
    charges_for_bill_period: Decimal
    vat: Decimal
    vas: Decimal
    add_to_bill_charges: Decimal
    late_payment_charges: Decimal


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