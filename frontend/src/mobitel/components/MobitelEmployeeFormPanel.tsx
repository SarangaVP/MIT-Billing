import { useState, type FormEvent } from "react";
import type { MobitelEmployee } from "../types/mobitel";
import { addMobitelConnection, removeMobitelConnection, setMobitelDefaultStaticIpCost } from "../api/mobitel";

interface Props {
  employee: MobitelEmployee | null;
  onSave: (payload: { emp_no: string; name: string; lob: string | null; lob_code?: string | null; mobile_no?: string | null }) => Promise<void>;
  onRefresh: () => void;
  onCancel: () => void;
}

export default function MobitelEmployeeFormPanel({ employee, onSave, onRefresh, onCancel }: Props) {
  const isEdit = employee !== null;
  const [empNo, setEmpNo] = useState(employee?.emp_no ?? "");
  const [name, setName] = useState(employee?.name ?? "");
  const [lob, setLob] = useState(employee?.lob ?? "");
  const [lobCode, setLobCode] = useState(employee?.lob_code ?? "");
  const [newMobileNo, setNewMobileNo] = useState("");
  const [staticIpDrafts, setStaticIpDrafts] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      await onSave({
        emp_no: empNo,
        name,
        lob: lob || null,
        lob_code: lobCode || null,
        ...(isEdit ? {} : { mobile_no: newMobileNo || null }),
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setSaving(false);
    }
  }

  async function handleAddConnection() {
    if (!employee || !newMobileNo) return;
    setError(null);
    try {
      await addMobitelConnection(employee.id, newMobileNo);
      setNewMobileNo("");
      onRefresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not add connection");
    }
  }

  async function handleRemoveConnection(connectionId: string) {
    if (!confirm("Remove this connection? It will be excluded from future bill splits.")) return;
    await removeMobitelConnection(connectionId);
    onRefresh();
  }

  async function handleSaveDefaultStaticIp(connectionId: string) {
    const draft = staticIpDrafts[connectionId];
    const cost = draft === undefined || draft === "" ? null : draft;
    setError(null);
    try {
      await setMobitelDefaultStaticIpCost(connectionId, cost);
      onRefresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save default static IP cost");
    }
  }

  return (
    <div className="panel-overlay" onClick={onCancel}>
      <form className="panel" onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
        <h2>{isEdit ? "Edit Mobitel employee" : "Add Mobitel employee"}</h2>
        {employee?.is_pool && <p className="field-hint">This is an unassigned "Pool" line — never billed.</p>}

        <label>
          EMP No
          <input required value={empNo} onChange={(e) => setEmpNo(e.target.value)} />
        </label>

        <label>
          Name
          <input required value={name} onChange={(e) => setName(e.target.value)} />
        </label>

        <label>
          LOB
          <input value={lob} onChange={(e) => setLob(e.target.value)} />
        </label>

        <label>
          LOB Code
          <input value={lobCode} onChange={(e) => setLobCode(e.target.value)} />
        </label>

        {!isEdit && (
          <label>
            Initial mobile no. <span className="field-hint">(optional)</span>
            <input value={newMobileNo} onChange={(e) => setNewMobileNo(e.target.value)} />
          </label>
        )}

        {isEdit && employee && (
          <div className="field-group">
            <span className="field-label">Connections</span>
            {employee.connections.length === 0 && <p className="field-hint">No connections yet.</p>}
            {employee.connections.map((c) => (
              <div key={c.id} className="inline-row" style={{ flexWrap: "wrap" }}>
                <span className="mono">{c.mobile_no}</span>
                <span className={`pill ${c.status === "active" ? "pill-active" : "pill-resigned"}`}>{c.status}</span>
                <input
                  type="number"
                  step="0.01"
                  placeholder="Default static IP (Rs.)"
                  style={{ width: 160 }}
                  value={staticIpDrafts[c.id] ?? c.default_static_ip_cost ?? ""}
                  onChange={(e) => setStaticIpDrafts((d) => ({ ...d, [c.id]: e.target.value }))}
                />
                <button type="button" className="link-btn" onClick={() => handleSaveDefaultStaticIp(c.id)}>
                  Save
                </button>
                <button type="button" className="link-btn link-btn-danger" onClick={() => handleRemoveConnection(c.id)}>
                  Remove
                </button>
              </div>
            ))}
            <div className="inline-row">
              <input
                placeholder="New mobile number"
                value={newMobileNo}
                onChange={(e) => setNewMobileNo(e.target.value)}
              />
              <button type="button" className="btn btn-ghost" onClick={handleAddConnection} disabled={!newMobileNo}>
                + Add
              </button>
            </div>
            <p className="field-hint">
              An employee can hold more than one connection — each is billed separately. "Default static IP" is
              applied automatically to every future bill import for that connection — leave blank for none.
            </p>
          </div>
        )}

        {error && <p className="form-error">{error}</p>}

        <div className="panel-actions">
          <button type="button" className="btn btn-ghost" onClick={onCancel}>
            {isEdit ? "Close" : "Cancel"}
          </button>
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? "Saving…" : isEdit ? "Save changes" : "Add employee"}
          </button>
        </div>
      </form>
    </div>
  );
}