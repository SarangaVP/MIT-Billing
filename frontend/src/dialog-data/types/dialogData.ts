// Mirrors backend/app/schemas/dialog_data_employee.py, dialog_data_bill.py
// NOTE: numeric fields are `string` — FastAPI/Pydantic serializes Decimal
// as a JSON string, not a number. Always Number(v) before arithmetic.

export type DialogDataConnectionStatus = "active" | "inactive";

export interface DialogDataConnection {
  id: string;
  connection_no: string;
  status: DialogDataConnectionStatus;
}

export interface DialogDataEmployee {
  id: string;
  emp_no: string;
  name: string;
  team: string | null;
  is_deleted: boolean;
  connections: DialogDataConnection[];
  created_at: string;
  updated_at: string;
}

export interface DialogDataEmployeeCreateInput {
  emp_no: string;
  name: string;
  team?: string | null;
  connection_no?: string | null;
}

export interface DialogDataEmployeeUpdateInput {
  emp_no?: string;
  name?: string;
  team?: string | null;
}

export interface DialogDataBillPeriod {
  id: string;
  label: string;
  invoice_no: string | null;
  mobile_no: string | null;
  invoice_date: string | null;
  period_start: string | null;
  period_end: string | null;
  data_charge: string | null;
  govt_taxes: string | null;
  vat: string | null;
  total: string | null;
  net: string | null;
  users_count: number | null;
  per_user_cost: string | null;
  reconciled: boolean;
  reconciliation_discrepancy: string | null;
  extraction_method: string;
  created_at: string;
}

export interface DialogDataImportResult {
  bill_period_id: string;
  line_items_created: number;
  users_count: number;
  net: string;
  per_user_cost: string;
  parsed_total: string;
  reconciled: boolean;
  reconciliation_discrepancy: string;
  extraction_method: string;
}

export interface DialogDataBillLineItemOut {
  id: string;
  connection_id: string;
  emp_no: string | null;
  name: string | null;
  team: string | null;
  connection_no: string | null;
  cost: string;
  allocation_gb: string | null;
  usage_gb: string | null;
  remaining_gb: string | null;
  pay_go_status: string | null;
  bill_cycle: string | null;
}