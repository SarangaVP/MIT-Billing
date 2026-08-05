// Mirrors backend/app/schemas/bill.py

export interface BillPeriod {
  id: string;
  label: string;
  corporate_code: string | null;
  bill_period_start: string | null;
  bill_period_end: string | null;
  invoice_date: string | null;
  stated_total_charges_for_bill_period: number | null;
  stated_total_due_amount: number | null;
  created_at: string;
}

export interface ImportResult {
  bill_period_id: string;
  line_items_imported: number;
  parsed_total_charges_for_bill_period: number;
  stated_total_charges_for_bill_period: number | null;
  reconciled: boolean;
}

export interface BillSummaryRow {
  bill_line_item_id: string;
  mobile_no: string;

  emp_no: string | null;
  name: string | null;
  lob: string | null;
  cadre: string | null;
  credit_limit: number | null;
  level: string | null;
  email: string | null;

  total_usage_charges: number;
  idd: number;
  roaming: number;
  vas: number;
  charges_for_bill_period: number;
  vat: number;
  add_to_bill_charges: number;

  net_amount: number;
  bucket_cost: number;
  bucket_vat: number;
  bucket_nett: number;
  total: number;
  salary_deduction: number;
  need_approval: string;
  is_overridden: boolean;
}

export interface ApprovalOverrideInput {
  approval_override: string | null;
}