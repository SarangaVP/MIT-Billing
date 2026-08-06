import type {
  MobitelEmployee,
  MobitelEmployeeCreateInput,
  MobitelEmployeeUpdateInput,
  MobitelBillPeriod,
  MobitelImportResult,
  MobitelBillLineItemOut,
  MobitelStaticIpRate,
  MobitelStaticIpRateCreateInput,
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

export function listMobitelBillPeriods(): Promise<MobitelBillPeriod[]> {
  return request<MobitelBillPeriod[]>("/mobitel/bills");
}

export async function importMobitelBill(label: string, file: File): Promise<MobitelImportResult> {
  const formData = new FormData();
  formData.append("label", label);
  formData.append("file", file);

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

export function listMobitelStaticIpRates(): Promise<MobitelStaticIpRate[]> {
  return request<MobitelStaticIpRate[]>("/mobitel/static-ip-rates");
}

export function createMobitelStaticIpRate(payload: MobitelStaticIpRateCreateInput): Promise<MobitelStaticIpRate> {
  return request<MobitelStaticIpRate>("/mobitel/static-ip-rates", { method: "POST", body: JSON.stringify(payload) });
}