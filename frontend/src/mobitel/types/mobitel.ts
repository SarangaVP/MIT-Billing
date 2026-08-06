// Mirrors backend/app/schemas/mobitel_employee.py, mobitel_bill.py, mobitel_static_ip_rate.py
// NOTE: numeric fields are `string` — FastAPI/Pydantic serializes Decimal as
// a JSON string, not a number. Always Number(v) before arithmetic.

export type MobitelEmployeeStatus = "active" | "inactive" | "pool";

export interface MobitelEmployee {
  id: string;
  emp_no: string;
  name: string;
  mobile_no: string;
  lob: string | null;
  status: MobitelEmployeeStatus;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
}

export interface MobitelEmployeeCreateInput {
  emp_no: string;
  name: string;
  mobile_no: string;
  lob?: string | null;
}

export interface MobitelEmployeeUpdateInput {
  emp_no?: string;
  name?: string;
  mobile_no?: string;
  lob?: string | null;
  status?: MobitelEmployeeStatus;
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
}

export interface MobitelBillLineItemOut {
  id: string;
  employee_id: string;
  emp_no: string | null;
  name: string | null;
  lob: string | null;
  mobile_no: string | null;
  data_cost: string;
  static_ip_cost: string;
  total: string;
}

export interface MobitelStaticIpRate {
  id: string;
  employee_id: string;
  employee_name: string | null;
  cost: string;
  effective_from: string;
  created_at: string;
}

export interface MobitelStaticIpRateCreateInput {
  employee_id: string;
  cost: string;
  effective_from: string;
}