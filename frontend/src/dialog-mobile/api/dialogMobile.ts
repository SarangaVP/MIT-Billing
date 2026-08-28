import type {
  DialogMobileEmployee,
  DialogMobileEmployeeCreateInput,
  DialogMobileEmployeeUpdateInput,
  DialogMobileEmployeeListFilters,
  DialogMobileMobileNumber,
  DialogMobileMobileNumberCreateInput,
  DialogMobileBillPeriod,
  DialogMobileImportResult,
  DialogMobileBillSummaryRow,
  DialogMobileApprovalOverrideInput,
  DialogMobileBucketExclusionInput,
  DialogMobileBucketRateOverrideInput,
  DialogMobileDataBucketSelectionInput,
  DialogMobileLineItemChargeUpdateInput,
} from "../types/dialogMobile";

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

  if (res.status === 204) return null as T;
  return res.json() as Promise<T>;
}

// Employees

export function listDialogMobileEmployees(filters: DialogMobileEmployeeListFilters = {}): Promise<DialogMobileEmployee[]> {
  const params = new URLSearchParams();
  if (filters.search) params.set("search", filters.search);
  if (filters.lob) params.set("lob", filters.lob);
  const qs = params.toString();
  return request<DialogMobileEmployee[]>(`/dialog-mobile/employees${qs ? `?${qs}` : ""}`);
}

export function createDialogMobileEmployee(payload: DialogMobileEmployeeCreateInput): Promise<DialogMobileEmployee> {
  return request<DialogMobileEmployee>("/dialog-mobile/employees", { method: "POST", body: JSON.stringify(payload) });
}

export function updateDialogMobileEmployee(id: string, payload: DialogMobileEmployeeUpdateInput): Promise<DialogMobileEmployee> {
  return request<DialogMobileEmployee>(`/dialog-mobile/employees/${id}`, { method: "PUT", body: JSON.stringify(payload) });
}

export function deleteDialogMobileEmployee(id: string): Promise<DialogMobileEmployee> {
  return request<DialogMobileEmployee>(`/dialog-mobile/employees/${id}`, { method: "DELETE" });
}

export function addDialogMobileMobileNumber(employeeId: string, payload: DialogMobileMobileNumberCreateInput): Promise<DialogMobileMobileNumber> {
  return request<DialogMobileMobileNumber>(`/dialog-mobile/employees/${employeeId}/mobile-numbers`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function removeDialogMobileMobileNumber(employeeId: string, numberId: string): Promise<DialogMobileMobileNumber> {
  return request<DialogMobileMobileNumber>(`/dialog-mobile/employees/${employeeId}/mobile-numbers/${numberId}`, {
    method: "DELETE",
  });
}

export function updateDialogMobileMobileNumberProjectLabel(numberId: string, projectLabel: string | null): Promise<DialogMobileMobileNumber> {
  return request<DialogMobileMobileNumber>(`/dialog-mobile/employees/mobile-numbers/${numberId}/project-label`, {
    method: "PUT",
    body: JSON.stringify({ project_label: projectLabel }),
  });
}

export async function importDialogMobileEmployeeSheet(file: File): Promise<any> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${BASE_URL}/dialog-mobile/employees/import`, { method: "POST", body: formData });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Import failed (${res.status})`);
  }
  return res.json();
}

// Bills

export function listDialogMobileBillPeriods(): Promise<DialogMobileBillPeriod[]> {
  return request<DialogMobileBillPeriod[]>("/dialog-mobile/bills");
}

export function getDialogMobileBillPeriod(id: string): Promise<DialogMobileBillPeriod> {
  return request<DialogMobileBillPeriod>(`/dialog-mobile/bills/${id}`);
}

export function getDialogMobileBillSummary(id: string): Promise<DialogMobileBillSummaryRow[]> {
  return request<DialogMobileBillSummaryRow[]>(`/dialog-mobile/bills/${id}/summary`);
}

export async function importDialogMobileBillPdf(label: string, file: File): Promise<DialogMobileImportResult> {
  const formData = new FormData();
  formData.append("label", label);
  formData.append("file", file);

  const res = await fetch(`${BASE_URL}/dialog-mobile/bills/import`, { method: "POST", body: formData });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Import failed (${res.status})`);
  }
  return res.json();
}

export function setDialogMobileApprovalOverride(lineItemId: string, payload: DialogMobileApprovalOverrideInput): Promise<DialogMobileBillSummaryRow> {
  return request<DialogMobileBillSummaryRow>(`/dialog-mobile/bills/line-items/${lineItemId}/approval-override`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function setDialogMobileBucketExclusion(lineItemId: string, payload: DialogMobileBucketExclusionInput): Promise<DialogMobileBillSummaryRow> {
  return request<DialogMobileBillSummaryRow>(`/dialog-mobile/bills/line-items/${lineItemId}/bucket-exclusion`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function setDialogMobileBucketRateOverride(billPeriodId: string, payload: DialogMobileBucketRateOverrideInput): Promise<DialogMobileBillSummaryRow[]> {
  return request<DialogMobileBillSummaryRow[]>(`/dialog-mobile/bills/${billPeriodId}/bucket-rate-override`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function setDialogMobileDataBucketNumber(billPeriodId: string, payload: DialogMobileDataBucketSelectionInput): Promise<DialogMobileBillSummaryRow[]> {
  return request<DialogMobileBillSummaryRow[]>(`/dialog-mobile/bills/${billPeriodId}/data-bucket-number`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function setDialogMobileLineItemCharges(lineItemId: string, payload: DialogMobileLineItemChargeUpdateInput): Promise<DialogMobileBillSummaryRow> {
  return request<DialogMobileBillSummaryRow>(`/dialog-mobile/bills/line-items/${lineItemId}/charges`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function deleteDialogMobileBillPeriod(billPeriodId: string): Promise<void> {
  const res = await fetch(`${BASE_URL}/dialog-mobile/bills/${billPeriodId}`, { method: "DELETE" });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Delete failed (${res.status})`);
  }
}