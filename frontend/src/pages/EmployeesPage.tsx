import { useEffect, useState, useCallback } from "react";
import type { Employee, EmployeeCreateInput, EmployeeUpdateInput } from "../types/employee";
import { listEmployees, createEmployee, updateEmployee, deleteEmployee } from "../api/employees";
import EmployeeFormPanel from "../components/EmployeeFormPanel";

export default function EmployeesPage() {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [search, setSearch] = useState("");
  const [lobFilter, setLobFilter] = useState("");

  const [formTarget, setFormTarget] = useState<Employee | "new" | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const data = await listEmployees({
        search: search || undefined,
        lob: lobFilter || undefined,
      });
      setEmployees(data);
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "Failed to load employees");
    } finally {
      setLoading(false);
    }
  }, [search, lobFilter]);

  useEffect(() => {
    const t = setTimeout(load, 250);
    return () => clearTimeout(t);
  }, [load]);

  // Keep an open Edit panel showing live data (e.g. after adding/removing a
  // mobile number inline) instead of a stale snapshot from when it opened.
  useEffect(() => {
    if (!formTarget || formTarget === "new") return;
    const fresh = employees.find((e) => e.id === formTarget.id);
    if (fresh) setFormTarget(fresh);
  }, [employees, formTarget === "new" ? null : formTarget?.id]);

  const lobOptions = [...new Set(employees.map((e) => e.lob).filter((v): v is string => Boolean(v)))].sort();

  async function handleSave(payload: EmployeeCreateInput | EmployeeUpdateInput) {
    if (formTarget && formTarget !== "new") {
      await updateEmployee(formTarget.id, payload as EmployeeUpdateInput);
    } else {
      await createEmployee(payload as EmployeeCreateInput);
      setFormTarget(null);
    }
    load();
  }

  async function handleDelete(employee: Employee) {
    if (!confirm(`Remove ${employee.name} from the employee list? Their billing history is kept.`)) return;
    await deleteEmployee(employee.id);
    load();
  }

  function activeNumbers(employee: Employee): string[] {
    return employee.mobile_numbers.filter((n) => n.status === "active").map((n) => n.mobile_no);
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Employees</h1>
          <p className="page-subtitle">Employee ↔ mobile number mapping used for monthly bill allocation.</p>
        </div>
        <button className="btn btn-primary" onClick={() => setFormTarget("new")}>
          + Add employee
        </button>
      </div>

      <div className="toolbar">
        <input
          className="search-input"
          placeholder="Search by name, EMP No, or mobile no…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select value={lobFilter} onChange={(e) => setLobFilter(e.target.value)}>
          <option value="">All LOBs</option>
          {lobOptions.map((lob) => (
            <option key={lob} value={lob}>
              {lob}
            </option>
          ))}
        </select>
      </div>

      {errorMsg && <div className="banner banner-error">{errorMsg}</div>}

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Mobile No</th>
              <th>EMP No</th>
              <th>Name</th>
              <th>LOB</th>
              <th>Cadre</th>
              <th>Credit Limit</th>
              <th>Level</th>
              <th>Email</th>
              <th>Resignation</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td colSpan={10} className="empty-row">
                  Loading…
                </td>
              </tr>
            )}
            {!loading && employees.length === 0 && (
              <tr>
                <td colSpan={10} className="empty-row">
                  No employees match these filters.
                </td>
              </tr>
            )}
            {!loading &&
              employees.map((emp) => (
                <tr key={emp.id}>
                  <td className="mono numbers-cell">
                    {activeNumbers(emp).length === 0 ? (
                      <span className="muted">—</span>
                    ) : (
                      activeNumbers(emp).map((n) => <span key={n}>{n}</span>)
                    )}
                  </td>
                  <td className="mono">{emp.emp_no}</td>
                  <td>{emp.name}</td>
                  <td>{emp.lob || <span className="muted">—</span>}</td>
                  <td>{emp.cadre || <span className="muted">—</span>}</td>
                  <td className="mono">
                    {emp.credit_limit != null ? `Rs. ${Number(emp.credit_limit).toLocaleString()}` : "—"}
                  </td>
                  <td>{emp.level || <span className="muted">—</span>}</td>
                  <td>{emp.email || <span className="muted">—</span>}</td>
                  <td>{emp.resignation || <span className="muted">—</span>}</td>
                  <td className="actions-cell">
                    <button className="link-btn" onClick={() => setFormTarget(emp)}>
                      Edit
                    </button>
                    <button className="link-btn link-btn-danger" onClick={() => handleDelete(emp)}>
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {formTarget !== null && (
        <EmployeeFormPanel
          employee={formTarget === "new" ? null : formTarget}
          onSave={handleSave}
          onNumbersChanged={load}
          onCancel={() => setFormTarget(null)}
        />
      )}
    </div>
  );
}