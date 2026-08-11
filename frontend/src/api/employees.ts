import type {
  Employee,
  EmployeeCreateInput,
  EmployeeUpdateInput,
  EmployeeListFilters,
  MobileNumber,
  MobileNumberCreateInput,
} from "../types/employee";

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

export function listEmployees(filters: EmployeeListFilters = {}): Promise<Employee[]> {
  const params = new URLSearchParams();
  if (filters.search) params.set("search", filters.search);
  if (filters.lob) params.set("lob", filters.lob);
  const qs = params.toString();
  return request<Employee[]>(`/employees${qs ? `?${qs}` : ""}`);
}

export function createEmployee(payload: EmployeeCreateInput): Promise<Employee> {
  return request<Employee>("/employees", { method: "POST", body: JSON.stringify(payload) });
}

export function updateEmployee(id: string, payload: EmployeeUpdateInput): Promise<Employee> {
  return request<Employee>(`/employees/${id}`, { method: "PUT", body: JSON.stringify(payload) });
}

export function deleteEmployee(id: string): Promise<Employee> {
  return request<Employee>(`/employees/${id}`, { method: "DELETE" });
}

export function addMobileNumber(employeeId: string, payload: MobileNumberCreateInput): Promise<MobileNumber> {
  return request<MobileNumber>(`/employees/${employeeId}/mobile-numbers`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function removeMobileNumber(employeeId: string, numberId: string): Promise<MobileNumber> {
  return request<MobileNumber>(`/employees/${employeeId}/mobile-numbers/${numberId}`, {
    method: "DELETE",
  });
}

export function updateMobileNumberProjectLabel(numberId: string, projectLabel: string | null): Promise<MobileNumber> {
  return request<MobileNumber>(`/employees/mobile-numbers/${numberId}/project-label`, {
    method: "PUT",
    body: JSON.stringify({ project_label: projectLabel }),
  });
}

export async function importEmployeeSheet(file: File): Promise<any> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${BASE_URL}/employees/import`, { method: "POST", body: formData });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Import failed (${res.status})`);
  }
  return res.json();
}