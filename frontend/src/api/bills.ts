import type { BillPeriod, ImportResult, BillSummaryRow, ApprovalOverrideInput } from "../types/bill";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, options);

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${res.status})`);
  }
  return res.json() as Promise<T>;
}

export function listBillPeriods(): Promise<BillPeriod[]> {
  return request<BillPeriod[]>("/bills");
}

export function getBillPeriod(id: string): Promise<BillPeriod> {
  return request<BillPeriod>(`/bills/${id}`);
}

export function getBillSummary(id: string): Promise<BillSummaryRow[]> {
  return request<BillSummaryRow[]>(`/bills/${id}/summary`);
}

export async function importBillPdf(label: string, file: File): Promise<ImportResult> {
  const formData = new FormData();
  formData.append("label", label);
  formData.append("file", file);

  const res = await fetch(`${BASE_URL}/bills/import`, { method: "POST", body: formData });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Import failed (${res.status})`);
  }
  return res.json();
}

export function setApprovalOverride(lineItemId: string, payload: ApprovalOverrideInput): Promise<BillSummaryRow> {
  return request<BillSummaryRow>(`/bills/line-items/${lineItemId}/approval-override`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function deleteBillPeriod(billPeriodId: string): Promise<void> {
  const res = await fetch(`${BASE_URL}/bills/${billPeriodId}`, { method: "DELETE" });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Delete failed (${res.status})`);
  }
}