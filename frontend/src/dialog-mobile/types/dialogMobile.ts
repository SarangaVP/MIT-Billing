// Mirrors backend/app/schemas/dialog_mobile_employee.py, dialog_mobile_mobile_number.py, dialog_mobile_bill.py
// NOTE: numeric fields are typed `string` because FastAPI/Pydantic
// serializes Decimal as a JSON string (to avoid float precision loss) —
// they are NOT native JSON numbers. Always wrap with Number(v) before
// doing arithmetic on two of these fields together.

export type DialogMobileMobileNumberStatus = "active" | "inactive";

export interface DialogMobileMobileNumber {
  id: string;
  mobile_no: string;
  is_primary: boolean;
  status: DialogMobileMobileNumberStatus;
  project_label: string | null;
  created_at: string;
}

export interface DialogMobileEmployee {
  id: string;
  emp_no: string;
  name: string;
  lob: string | null;
  lob_code: string | null;
  cadre: string | null;
  credit_limit: number | null;
  level: string | null;
  email: string | null;
  resignation: string | null; // free text, e.g. "No" or a date — matches source sheet
  is_deleted: boolean;
  is_general_line: boolean;
  created_at: string;
  updated_at: string;
  mobile_numbers: DialogMobileMobileNumber[];
}

export interface DialogMobileEmployeeCreateInput {
  emp_no: string;
  name: string;
  mobile_no?: string | null; // optional — some employees have no number at all
  lob?: string | null;
  lob_code?: string | null;
  cadre?: string | null;
  credit_limit?: number | null;
  level?: string | null;
  email?: string | null;
  resignation?: string | null;
}

export interface DialogMobileEmployeeUpdateInput {
  emp_no?: string;
  name?: string;
  lob?: string | null;
  lob_code?: string | null;
  cadre?: string | null;
  credit_limit?: number | null;
  level?: string | null;
  email?: string | null;
  resignation?: string | null;
}

export interface DialogMobileMobileNumberCreateInput {
  mobile_no: string;
  is_primary?: boolean;
}

export interface DialogMobileEmployeeListFilters {
  search?: string;
  lob?: string;
}

// --- Bills ---

export type DialogMobileSourceFormat = "pdf" | "xls";

export interface DialogMobileBillPeriod {
  id: string;
  label: string;
  corporate_code: string | null;
  bill_period_start: string | null;
  bill_period_end: string | null;
  invoice_date: string | null;
  stated_total_charges_for_bill_period: string | null;
  stated_total_due_amount: string | null;
  source_format: DialogMobileSourceFormat;
  reconciled: boolean;
  reconciliation_discrepancy: string | null;
  data_bucket_mobile_no: string | null;
  created_at: string;
}

export interface DialogMobileImportResult {
  bill_period_id: string;
  line_items_imported: number;
  parsed_total_charges_for_bill_period: string;
  stated_total_charges_for_bill_period: string | null;
  reconciled: boolean;
  reconciliation_discrepancy: string | null;
  source_format: DialogMobileSourceFormat;
  // Connections whose source file had a value too large to store (e.g. a
  // broken/circular Excel formula) — that specific field was reset to 0
  // so the import could still complete without dropping the connection
  // from the bill. Empty in the normal case.
  corrupted_value_warnings: string[];
  // True when the usual data bucket connection (765155535) was found and
  // automatically selected for this bill period — no manual click needed.
  data_bucket_auto_selected: boolean;
  // Mobile numbers automatically marked bucket-excluded on import (the
  // recurring Security 1/3/4 lines, plus the data bucket connection
  // itself if selected). Still fully editable via "Manage bucket exclusion".
  auto_bucket_excluded_mobile_nos: string[];
}

export interface DialogMobileBillSummaryRow {
  bill_line_item_id: string;
  mobile_no: string;

  emp_no: string | null;
  name: string | null;
  lob: string | null;
  lob_code: string | null;
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
  late_payment_charges: string;

  net_amount: string;
  bucket_cost: string;
  bucket_vat: string;
  bucket_nett: string;
  total: string;
  salary_deduction: string;
  is_salary_deduction_overridden: boolean;
  need_approval: string;
  is_overridden: boolean;
  is_general_line: boolean;
  is_bucket_excluded: boolean;
  is_data_bucket_line: boolean;
  eligible_employee_count: number;
  standard_bucket_cost: string;
  standard_bucket_vat: string;
  standard_bucket_nett: string;
}

export interface DialogMobileApprovalOverrideInput {
  approval_override: string | null;
}

export interface DialogMobileSalaryDeductionOverrideInput {
  salary_deduction_override: number | null;
}

export interface DialogMobileBucketExclusionInput {
  is_bucket_excluded: boolean;
}

export interface DialogMobileDataBucketSelectionInput {
  data_bucket_mobile_no: string | null;
}

export interface DialogMobileLineItemChargeUpdateInput {
  total_usage_charges: number;
  idd: number;
  roaming: number;
  charges_for_bill_period: number;
  vat: number;
  vas: number;
  add_to_bill_charges: number;
  late_payment_charges: number;
}