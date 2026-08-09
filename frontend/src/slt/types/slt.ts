// Mirrors backend/app/schemas/slt_bill.py, slt_general_bill.py
// NOTE: numeric fields are `string` — FastAPI/Pydantic serializes Decimal
// as a JSON string, not a number. Always Number(v) before arithmetic.

// --- Team Package (account 004 767 150X) ---

export interface SltTeamPackageBillPeriod {
  id: string;
  label: string;
  account_no: string | null;
  invoice_no: string | null;
  billing_date: string | null;
  period_start: string | null;
  period_end: string | null;
  due_date: string | null;
  balance_bf: string | null;
  payments_received: string | null;
  cess: string | null;
  sscl: string | null;
  vat: string | null;
  charges_for_period: string | null;
  total_payable: string | null;
  users_count: number | null;
  package_sum: string | null;
  reconciled: boolean;
  reconciliation_discrepancy: string | null;
  extraction_method: string;
  created_at: string;
}

export interface SltTeamPackageImportResult {
  bill_period_id: string;
  line_items_created: number;
  users_count: number;
  package_sum: string;
  charges_for_period: string;
  computed_total: string;
  reconciled: boolean;
  reconciliation_discrepancy: string;
}

export interface SltTeamPackageBillLineItem {
  id: string;
  name: string;
  team: string | null;
  lob_code: string | null;
  package_name: string;
  package_price: string;
}

// --- General bills (4 fixed accounts) ---

export interface SltGeneralAccount {
  id: string;
  account_no: string;
  label: string;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
}

export interface SltGeneralBillPeriod {
  id: string;
  account_id: string;
  account_no: string | null;
  account_label: string | null;
  label: string;
  invoice_no: string | null;
  billing_date: string | null;
  period_start: string | null;
  period_end: string | null;
  due_date: string | null;
  balance_bf: string | null;
  payments_received: string | null;
  charges_for_period: string | null;
  total_payable: string | null;
  line_items_sum: string | null;
  extraction_discrepancy: string | null;
  extraction_method: string;
  created_at: string;
}

export interface SltGeneralBillLineItem {
  id: string;
  description: string;
  amount: string;
}

export interface SltGeneralImportOneResult {
  filename: string;
  success: boolean;
  bill_period_id: string | null;
  account_no: string | null;
  account_label: string | null;
  charges_for_period: string | null;
  line_items_sum: string | null;
  error: string | null;
}

export interface SltGeneralImportBatchResult {
  results: SltGeneralImportOneResult[];
}