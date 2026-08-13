import type {
  DialogDataEmployee,
  DialogDataEmployeeCreateInput,
  DialogDataEmployeeUpdateInput,
  DialogDataBillPeriod,
  DialogDataImportResult,
  DialogDataBillLineItemOut,
} from "../types/dialogData";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${res.status})`);
  }
  return res.json() as Promise<T>;
}

// Employees

export function listDialogDataEmployees(search?: string): Promise<DialogDataEmployee[]> {
  const qs = search ? `?search=${encodeURIComponent(search)}` : "";
  return request<DialogDataEmployee[]>(`/dialog-data/employees${qs}`);
}

export function createDialogDataEmployee(payload: DialogDataEmployeeCreateInput): Promise<DialogDataEmployee> {
  return request<DialogDataEmployee>("/dialog-data/employees", { method: "POST", body: JSON.stringify(payload) });
}

export function updateDialogDataEmployee(id: string, payload: DialogDataEmployeeUpdateInput): Promise<DialogDataEmployee> {
  return request<DialogDataEmployee>(`/dialog-data/employees/${id}`, { method: "PUT", body: JSON.stringify(payload) });
}

export function deleteDialogDataEmployee(id: string): Promise<DialogDataEmployee> {
  return request<DialogDataEmployee>(`/dialog-data/employees/${id}`, { method: "DELETE" });
}

export function addDialogDataConnection(employeeId: string, connectionNo: string): Promise<DialogDataEmployee> {
  return request<DialogDataEmployee>(`/dialog-data/employees/${employeeId}/connections`, {
    method: "POST",
    body: JSON.stringify({ connection_no: connectionNo }),
  });
}

export async function removeDialogDataConnection(connectionId: string): Promise<void> {
  const res = await fetch(`${BASE_URL}/dialog-data/employees/connections/${connectionId}`, { method: "DELETE" });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Delete failed (${res.status})`);
  }
}

// Bills

export function listDialogDataBillPeriods(): Promise<DialogDataBillPeriod[]> {
  return request<DialogDataBillPeriod[]>("/dialog-data/bills");
}

export async function importDialogDataBill(
  label: string,
  file: File,
  billSheetFile?: File | null
): Promise<DialogDataImportResult> {
  const formData = new FormData();
  formData.append("label", label);
  formData.append("file", file);
  if (billSheetFile) {
    formData.append("bill_sheet_file", billSheetFile);
  }

  const res = await fetch(`${BASE_URL}/dialog-data/bills/import`, { method: "POST", body: formData });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Import failed (${res.status})`);
  }
  return res.json();
}

export function getDialogDataBillSummary(billPeriodId: string): Promise<DialogDataBillLineItemOut[]> {
  return request<DialogDataBillLineItemOut[]>(`/dialog-data/bills/${billPeriodId}/summary`);
}

export function setDialogDataProjectCost(lineItemId: string, isProjectCost: boolean, projectCostAmount: string | null): Promise<DialogDataBillLineItemOut[]> {
  return request<DialogDataBillLineItemOut[]>(`/dialog-data/bills/line-items/${lineItemId}/project-cost`, {
    method: "PUT",
    body: JSON.stringify({ is_project_cost: isProjectCost, project_cost_amount: projectCostAmount }),
  });
}

export async function deleteDialogDataBillPeriod(billPeriodId: string): Promise<void> {
  const res = await fetch(`${BASE_URL}/dialog-data/bills/${billPeriodId}`, { method: "DELETE" });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Delete failed (${res.status})`);
  }
}

export async function importDialogDataEmployeeSheet(file: File): Promise<any> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${BASE_URL}/dialog-data/employees/import`, { method: "POST", body: formData });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Import failed (${res.status})`);
  }
  return res.json();
}