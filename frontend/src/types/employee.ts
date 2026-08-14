// These mirror backend/app/schemas/employee.py and mobile_number.py.
// Keep them in sync manually — if the backend schema changes, update here too.

export type MobileNumberStatus = "active" | "inactive";

export interface MobileNumber {
  id: string;
  mobile_no: string;
  is_primary: boolean;
  status: MobileNumberStatus;
  project_label: string | null;
  created_at: string;
}

export interface Employee {
  id: string;
  emp_no: string;
  name: string;
  lob: string | null;
  cadre: string | null;
  credit_limit: number | null;
  level: string | null;
  email: string | null;
  resignation: string | null; // free text, e.g. "No" or a date — matches source sheet
  is_deleted: boolean;
  is_general_line: boolean;
  created_at: string;
  updated_at: string;
  mobile_numbers: MobileNumber[];
}

export interface EmployeeCreateInput {
  emp_no: string;
  name: string;
  mobile_no?: string | null; // optional — some employees have no number at all
  lob?: string | null;
  cadre?: string | null;
  credit_limit?: number | null;
  level?: string | null;
  email?: string | null;
  resignation?: string | null;
}

export interface EmployeeUpdateInput {
  emp_no?: string;
  name?: string;
  lob?: string | null;
  cadre?: string | null;
  credit_limit?: number | null;
  level?: string | null;
  email?: string | null;
  resignation?: string | null;
}

export interface MobileNumberCreateInput {
  mobile_no: string;
  is_primary?: boolean;
}

export interface EmployeeListFilters {
  search?: string;
  lob?: string;
}