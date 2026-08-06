import { useEffect, useState, useCallback, type FormEvent } from "react";
import type { MobitelStaticIpRate, MobitelEmployee } from "../types/mobitel";
import { listMobitelStaticIpRates, createMobitelStaticIpRate, listMobitelEmployees } from "../api/mobitel";

export default function MobitelSettingsPage() {
  const [rates, setRates] = useState<MobitelStaticIpRate[]>([]);
  const [employees, setEmployees] = useState<MobitelEmployee[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);

  const [employeeId, setEmployeeId] = useState("");
  const [cost, setCost] = useState("1500");
  const [effectiveFrom, setEffectiveFrom] = useState(() => new Date().toISOString().slice(0, 10));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [rateData, employeeData] = await Promise.all([listMobitelStaticIpRates(), listMobitelEmployees()]);
      setRates(rateData);
      setEmployees(employeeData);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      await createMobitelStaticIpRate({ employee_id: employeeId, cost, effective_from: effectiveFrom });
      setShowForm(false);
      setEmployeeId("");
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Mobitel Settings</h1>
          <p className="page-subtitle">
            Static IP costs — a rare per-employee add-on charge, not present in any bill file.
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowForm(true)}>
          + Add static IP rate
        </button>
      </div>

      {loading && <p className="field-hint">Loading…</p>}

      {!loading && rates.length === 0 && (
        <div className="banner banner-error">No static IP rates set. Every employee's data cost will be the same.</div>
      )}

      {!loading && rates.length > 0 && (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Employee</th>
                <th>Cost</th>
                <th>Effective from</th>
              </tr>
            </thead>
            <tbody>
              {rates.map((r) => (
                <tr key={r.id}>
                  <td>{r.employee_name || <span className="muted">—</span>}</td>
                  <td className="mono">Rs. {Number(r.cost).toLocaleString()}</td>
                  <td className="mono">{r.effective_from}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showForm && (
        <div className="panel-overlay" onClick={() => setShowForm(false)}>
          <form className="panel panel-small" onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
            <h2>Add a static IP rate</h2>
            <p className="field-hint">
              Adds a new rate effective from the date below — past bills keep using whatever rate was active then.
            </p>

            <label>
              Employee
              <select required value={employeeId} onChange={(e) => setEmployeeId(e.target.value)}>
                <option value="" disabled>
                  Select employee…
                </option>
                {employees.map((emp) => (
                  <option key={emp.id} value={emp.id}>
                    {emp.name} ({emp.emp_no})
                  </option>
                ))}
              </select>
            </label>

            <label>
              Cost (Rs.)
              <input type="number" step="0.01" required value={cost} onChange={(e) => setCost(e.target.value)} />
            </label>

            <label>
              Effective from
              <input type="date" required value={effectiveFrom} onChange={(e) => setEffectiveFrom(e.target.value)} />
            </label>

            {error && <p className="form-error">{error}</p>}

            <div className="panel-actions">
              <button type="button" className="btn btn-ghost" onClick={() => setShowForm(false)}>
                Cancel
              </button>
              <button type="submit" className="btn btn-primary" disabled={saving}>
                {saving ? "Saving…" : "Save"}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}