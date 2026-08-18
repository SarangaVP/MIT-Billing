import type {
  MobitelEmployee,
  MobitelEmployeeCreateInput,
  MobitelEmployeeUpdateInput,
  MobitelBillPeriod,
  MobitelImportResult,
  MobitelBillLineItemOut,
  MobitelConnection,
} from "../types/mobitel";

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

export function listMobitelEmployees(search?: string): Promise<MobitelEmployee[]> {
  const qs = search ? `?search=${encodeURIComponent(search)}` : "";
  return request<MobitelEmployee[]>(`/mobitel/employees${qs}`);
}

export function createMobitelEmployee(payload: MobitelEmployeeCreateInput): Promise<MobitelEmployee> {
  return request<MobitelEmployee>("/mobitel/employees", { method: "POST", body: JSON.stringify(payload) });
}

export function updateMobitelEmployee(id: string, payload: MobitelEmployeeUpdateInput): Promise<MobitelEmployee> {
  return request<MobitelEmployee>(`/mobitel/employees/${id}`, { method: "PUT", body: JSON.stringify(payload) });
}

export function deleteMobitelEmployee(id: string): Promise<MobitelEmployee> {
  return request<MobitelEmployee>(`/mobitel/employees/${id}`, { method: "DELETE" });
}

export function addMobitelConnection(employeeId: string, mobileNo: string): Promise<MobitelEmployee> {
  return request<MobitelEmployee>(`/mobitel/employees/${employeeId}/connections`, {
    method: "POST",
    body: JSON.stringify({ mobile_no: mobileNo }),
  });
}

export async function removeMobitelConnection(connectionId: string): Promise<void> {
  const res = await fetch(`${BASE_URL}/mobitel/employees/connections/${connectionId}`, { method: "DELETE" });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Delete failed (${res.status})`);
  }
}

export function setMobitelDefaultStaticIpCost(connectionId: string, cost: string | null): Promise<MobitelConnection> {
  return request<MobitelConnection>(`/mobitel/employees/connections/${connectionId}/default-static-ip-cost`, {
    method: "PUT",
    body: JSON.stringify({ default_static_ip_cost: cost }),
  });
}

// Bills

export function listMobitelBillPeriods(): Promise<MobitelBillPeriod[]> {
  return request<MobitelBillPeriod[]>("/mobitel/bills");
}

export async function importMobitelBill(label: string, file: File, portalFile?: File | null): Promise<MobitelImportResult> {
  const formData = new FormData();
  formData.append("label", label);
  formData.append("file", file);
  if (portalFile) {
    formData.append("portal_file", portalFile);
  }

  const res = await fetch(`${BASE_URL}/mobitel/bills/import`, { method: "POST", body: formData });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Import failed (${res.status})`);
  }
  return res.json();
}

export function getMobitelBillSummary(billPeriodId: string): Promise<MobitelBillLineItemOut[]> {
  return request<MobitelBillLineItemOut[]>(`/mobitel/bills/${billPeriodId}/summary`);
}

// Sets one line item's static IP cost for its bill period, and returns the
// WHOLE recalculated summary — every row's data_cost/total may change,
// since the per-user split depends on everyone's static IP cost together.
export function setMobitelStaticIpCost(lineItemId: string, cost: string): Promise<MobitelBillLineItemOut[]> {
  return request<MobitelBillLineItemOut[]>(`/mobitel/bills/line-items/${lineItemId}/static-ip-cost`, {
    method: "PUT",
    body: JSON.stringify({ cost }),
  });
}

export function setMobitelProjectCost(lineItemId: string, isProjectCost: boolean, projectCostAmount: string | null): Promise<MobitelBillLineItemOut[]> {
  return request<MobitelBillLineItemOut[]>(`/mobitel/bills/line-items/${lineItemId}/project-cost`, {
    method: "PUT",
    body: JSON.stringify({ is_project_cost: isProjectCost, project_cost_amount: projectCostAmount }),
  });
}

export async function deleteMobitelBillPeriod(billPeriodId: string): Promise<void> {
  const res = await fetch(`${BASE_URL}/mobitel/bills/${billPeriodId}`, { method: "DELETE" });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Delete failed (${res.status})`);
  }
}

export async function importMobitelEmployeeSheet(file: File): Promise<any> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${BASE_URL}/mobitel/employees/import`, { method: "POST", body: formData });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Import failed (${res.status})`);
  }
  return res.json();
}