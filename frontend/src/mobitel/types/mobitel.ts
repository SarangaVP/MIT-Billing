// Mirrors backend/app/schemas/mobitel_employee.py, mobitel_bill.py
// NOTE: numeric fields are `string` — FastAPI/Pydantic serializes Decimal as
// a JSON string, not a number. Always Number(v) before arithmetic.

export type MobitelConnectionStatus = "active" | "inactive";

export interface MobitelConnection {
  id: string;
  mobile_no: string;
  status: MobitelConnectionStatus;
}

export interface MobitelEmployee {
  id: string;
  emp_no: string;
  name: string;
  lob: string | null;
  lob_code: string | null;
  is_pool: boolean;
  is_deleted: boolean;
  connections: MobitelConnection[];
  created_at: string;
  updated_at: string;
}

export interface MobitelEmployeeCreateInput {
  emp_no: string;
  name: string;
  lob?: string | null;
  lob_code?: string | null;
  mobile_no?: string | null;   // optional initial connection
}

export interface MobitelEmployeeUpdateInput {
  emp_no?: string;
  name?: string;
  lob?: string | null;
  lob_code?: string | null;
}

export interface MobitelBillPeriod {
  id: string;
  label: string;
  bill_no: string | null;
  account_no: string | null;
  bill_date: string | null;
  due_date: string | null;
  period_start: string | null;
  period_end: string | null;
  arrears: string | null;
  bucket_total: string | null;
  vat: string | null;
  net: string | null;
  total_payable: string | null;
  users_count: number | null;
  per_user_cost: string | null;
  reconciled: boolean;
  reconciliation_discrepancy: string | null;
  created_at: string;
}

export interface MobitelImportResult {
  bill_period_id: string;
  line_items_created: number;
  users_count: number;
  net: string;
  per_user_cost: string;
  parsed_total: string;
  reconciled: boolean;
  reconciliation_discrepancy: string;
  extraction_method: string;
  unmatched_in_portal_sheet: string[];
}

export interface MobitelBillLineItemOut {
  id: string;
  connection_id: string;
  emp_no: string | null;
  name: string | null;
  lob: string | null;
  lob_code: string | null;
  mobile_no: string | null;
  data_cost: string;
  static_ip_cost: string;
  is_project_cost: boolean;
  project_cost_amount: string | null;
  project_label: string | null;
  total: string;
  imsi_number: string | null;
  data_volume_mb: string | null;
  available_data_volume_mb: string | null;
  utilized_data_volume_mb: string | null;
  daily_limit_mb: string | null;
  utilized_daily_limit_mb: string | null;
  member_status: string | null;
  top_up_mb: string | null;
  utilized_topup_mb: string | null;
}