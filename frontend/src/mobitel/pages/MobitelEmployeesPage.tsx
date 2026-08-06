import { useEffect, useState, useCallback } from "react";
import type { MobitelEmployee, MobitelEmployeeCreateInput, MobitelEmployeeUpdateInput } from "../types/mobitel";
import { listMobitelEmployees, createMobitelEmployee, updateMobitelEmployee, deleteMobitelEmployee } from "../api/mobitel";
import MobitelEmployeeFormPanel from "../components/MobitelEmployeeFormPanel";

export default function MobitelEmployeesPage() {
  const [employees, setEmployees] = useState<MobitelEmployee[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [formTarget, setFormTarget] = useState<MobitelEmployee | "new" | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      setEmployees(await listMobitelEmployees(search || undefined));
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "Failed to load employees");
    } finally {
      setLoading(false);
    }
  }, [search]);

  useEffect(() => {
    const t = setTimeout(load, 250);
    return () => clearTimeout(t);
  }, [load]);

  useEffect(() => {
    if (!formTarget || formTarget === "new") return;
    const fresh = employees.find((e) => e.id === formTarget.id);
    if (fresh) setFormTarget(fresh);
  }, [employees, formTarget === "new" ? null : formTarget?.id]);

  async function handleSave(payload: MobitelEmployeeCreateInput | MobitelEmployeeUpdateInput) {
    if (formTarget && formTarget !== "new") {
      await updateMobitelEmployee(formTarget.id, payload as MobitelEmployeeUpdateInput);
    } else {
      await createMobitelEmployee(payload as MobitelEmployeeCreateInput);
      setFormTarget(null);
    }
    load();
  }

  async function handleDelete(employee: MobitelEmployee) {
    if (!confirm(`Remove ${employee.name} from Mobitel employees? Their billing history is kept.`)) return;
    await deleteMobitelEmployee(employee.id);
    load();
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Mobitel Employees</h1>
          <p className="page-subtitle">Employees holding a Mobitel data bucket line.</p>
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
      </div>

      {errorMsg && <div className="banner banner-error">{errorMsg}</div>}

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>EMP No</th>
              <th>Name</th>
              <th>Mobile No</th>
              <th>LOB</th>
              <th>Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td colSpan={6} className="empty-row">
                  Loading…
                </td>
              </tr>
            )}
            {!loading && employees.length === 0 && (
              <tr>
                <td colSpan={6} className="empty-row">
                  No employees match.
                </td>
              </tr>
            )}
            {!loading &&
              employees.map((emp) => (
                <tr key={emp.id}>
                  <td className="mono">{emp.emp_no}</td>
                  <td>{emp.name}</td>
                  <td className="mono">{emp.mobile_no}</td>
                  <td>{emp.lob || <span className="muted">—</span>}</td>
                  <td>
                    <span
                      className={`pill ${
                        emp.status === "active" ? "pill-active" : emp.status === "pool" ? "pill-transferred" : "pill-resigned"
                      }`}
                    >
                      {emp.status === "active" ? "Active" : emp.status === "pool" ? "Pool (unassigned)" : "Inactive"}
                    </span>
                  </td>
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
        <MobitelEmployeeFormPanel
          employee={formTarget === "new" ? null : formTarget}
          onSave={handleSave}
          onCancel={() => setFormTarget(null)}
        />
      )}
    </div>
  );
}