// Mirrors backend/app/schemas/bill.py
// NOTE: numeric fields are typed `string` because FastAPI/Pydantic
// serializes Decimal as a JSON string (to avoid float precision loss) —
// they are NOT native JSON numbers. Always wrap with Number(v) before
// doing arithmetic on two of these fields together.

export type SourceFormat = "pdf" | "xls";

export interface BillPeriod {
  id: string;
  label: string;
  corporate_code: string | null;
  bill_period_start: string | null;
  bill_period_end: string | null;
  invoice_date: string | null;
  stated_total_charges_for_bill_period: string | null;
  stated_total_due_amount: string | null;
  source_format: SourceFormat;
  reconciled: boolean;
  reconciliation_discrepancy: string | null;
  bucket_cost_override: string | null;
  bucket_vat_override: string | null;
  created_at: string;
}

export interface ImportResult {
  bill_period_id: string;
  line_items_imported: number;
  parsed_total_charges_for_bill_period: string;
  stated_total_charges_for_bill_period: string | null;
  reconciled: boolean;
  reconciliation_discrepancy: string | null;
  source_format: SourceFormat;
}

export interface BillSummaryRow {
  bill_line_item_id: string;
  mobile_no: string;

  emp_no: string | null;
  name: string | null;
  lob: string | null;
  cadre: string | null;
  credit_limit: string | null;
  level: string | null;
  email: string | null;
  project_label: string | null;

  total_usage_charges: string;
  // Only populated when the bill was imported from the .xls source —
  // null for PDF-sourced imports, which only give the combined total above.
  voice_rental: string | null;
  voice_usage: string | null;
  sms: string | null;
  data_rental: string | null;
  data_usage: string | null;

  idd: string;
  roaming: string;
  vas: string;
  charges_for_bill_period: string;
  vat: string;
  add_to_bill_charges: string;

  net_amount: string;
  bucket_cost: string;
  bucket_vat: string;
  bucket_nett: string;
  total: string;
  salary_deduction: string;
  need_approval: string;
  is_overridden: boolean;
  is_general_line: boolean;
  is_bucket_excluded: boolean;
}

export interface ApprovalOverrideInput {
  approval_override: string | null;
}

export interface BucketExclusionInput {
  is_bucket_excluded: boolean;
}

export interface BucketRateOverrideInput {
  bucket_cost_override: number | null;
  bucket_vat_override: number | null;
}