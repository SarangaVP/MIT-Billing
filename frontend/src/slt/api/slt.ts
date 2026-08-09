import type {
  SltTeamPackageBillPeriod,
  SltTeamPackageImportResult,
  SltTeamPackageBillLineItem,
  SltGeneralAccount,
  SltGeneralBillPeriod,
  SltGeneralBillLineItem,
  SltGeneralImportBatchResult,
} from "../types/slt";

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

// --- Team Package ---

export function listSltTeamPackageBillPeriods(): Promise<SltTeamPackageBillPeriod[]> {
  return request<SltTeamPackageBillPeriod[]>("/slt/team-package/bills");
}

export async function importSltTeamPackageBill(
  label: string,
  file: File,
  excelFile: File
): Promise<SltTeamPackageImportResult> {
  const formData = new FormData();
  formData.append("label", label);
  formData.append("file", file);
  formData.append("excel_file", excelFile);

  const res = await fetch(`${BASE_URL}/slt/team-package/bills/import`, { method: "POST", body: formData });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Import failed (${res.status})`);
  }
  return res.json();
}

export function getSltTeamPackageBillSummary(billPeriodId: string): Promise<SltTeamPackageBillLineItem[]> {
  return request<SltTeamPackageBillLineItem[]>(`/slt/team-package/bills/${billPeriodId}/summary`);
}

export async function deleteSltTeamPackageBillPeriod(billPeriodId: string): Promise<void> {
  const res = await fetch(`${BASE_URL}/slt/team-package/bills/${billPeriodId}`, { method: "DELETE" });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Delete failed (${res.status})`);
  }
}

// --- General bills ---

export function listSltGeneralAccounts(): Promise<SltGeneralAccount[]> {
  return request<SltGeneralAccount[]>("/slt/general/accounts");
}

export function updateSltGeneralAccountLabel(accountId: string, label: string): Promise<SltGeneralAccount> {
  return request<SltGeneralAccount>(`/slt/general/accounts/${accountId}`, {
    method: "PUT",
    body: JSON.stringify({ label }),
  });
}

export async function deleteSltGeneralAccount(accountId: string): Promise<void> {
  const res = await fetch(`${BASE_URL}/slt/general/accounts/${accountId}`, { method: "DELETE" });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Delete failed (${res.status})`);
  }
}

export function listSltGeneralBillPeriods(): Promise<SltGeneralBillPeriod[]> {
  return request<SltGeneralBillPeriod[]>("/slt/general/bills");
}

export async function importSltGeneralBills(label: string, files: File[]): Promise<SltGeneralImportBatchResult> {
  const formData = new FormData();
  formData.append("label", label);
  files.forEach((file) => formData.append("files", file));

  const res = await fetch(`${BASE_URL}/slt/general/bills/import`, { method: "POST", body: formData });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Import failed (${res.status})`);
  }
  return res.json();
}

export function getSltGeneralBillLineItems(billPeriodId: string): Promise<SltGeneralBillLineItem[]> {
  return request<SltGeneralBillLineItem[]>(`/slt/general/bills/${billPeriodId}/line-items`);
}

export async function deleteSltGeneralBillPeriod(billPeriodId: string): Promise<void> {
  const res = await fetch(`${BASE_URL}/slt/general/bills/${billPeriodId}`, { method: "DELETE" });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Delete failed (${res.status})`);
  }
}