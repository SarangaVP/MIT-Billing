import { useEffect, useState, useCallback } from "react";
import type { DialogDataEmployee } from "../types/dialogData";
import { listDialogDataEmployees, createDialogDataEmployee, updateDialogDataEmployee, deleteDialogDataEmployee } from "../api/dialogData";
import DialogDataEmployeeFormPanel from "../components/DialogDataEmployeeFormPanel";

export default function DialogDataEmployeesPage() {
  const [employees, setEmployees] = useState<DialogDataEmployee[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [formTarget, setFormTarget] = useState<DialogDataEmployee | "new" | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      setEmployees(await listDialogDataEmployees(search || undefined));
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

  async function handleSave(payload: { emp_no: string; name: string; team: string | null; lob_code?: string | null; connection_no?: string | null }) {
    if (formTarget && formTarget !== "new") {
      await updateDialogDataEmployee(formTarget.id, { emp_no: payload.emp_no, name: payload.name, team: payload.team, lob_code: payload.lob_code });
    } else {
      await createDialogDataEmployee(payload);
      setFormTarget(null);
    }
    load();
  }

  async function handleDelete(employee: DialogDataEmployee) {
    if (!confirm(`Remove ${employee.name} from Dialog Data Bucket employees? Their billing history is kept.`)) return;
    await deleteDialogDataEmployee(employee.id);
    load();
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Dialog Data Bucket Employees</h1>
          <p className="page-subtitle">Employees holding one or more Dialog Data Bucket connections.</p>
        </div>
        <button className="btn btn-primary" onClick={() => setFormTarget("new")}>
          + Add employee
        </button>
      </div>

      <div className="toolbar">
        <input
          className="search-input"
          placeholder="Search by name or EMP No…"
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
              <th>Team</th>
              <th>LOB Code</th>
              <th>Connections</th>
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
                  <td>{emp.team || <span className="muted">—</span>}</td>
                  <td className="mono">{emp.lob_code || <span className="muted">—</span>}</td>
                  <td className="mono">
                    {emp.connections.length === 0 ? (
                      <span className="muted">None</span>
                    ) : (
                      emp.connections.map((c) => c.connection_no).join(", ")
                    )}
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
        <DialogDataEmployeeFormPanel
          employee={formTarget === "new" ? null : formTarget}
          onSave={handleSave}
          onRefresh={load}
          onCancel={() => setFormTarget(null)}
        />
      )}
    </div>
  );
}