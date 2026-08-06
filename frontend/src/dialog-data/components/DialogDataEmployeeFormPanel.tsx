import { useState, type FormEvent } from "react";
import type { DialogDataEmployee } from "../types/dialogData";
import { addDialogDataConnection, removeDialogDataConnection } from "../api/dialogData";

interface Props {
  employee: DialogDataEmployee | null;
  onSave: (payload: { emp_no: string; name: string; team: string | null; connection_no?: string | null }) => Promise<void>;
  onRefresh: () => void;
  onCancel: () => void;
}

export default function DialogDataEmployeeFormPanel({ employee, onSave, onRefresh, onCancel }: Props) {
  const isEdit = employee !== null;
  const [empNo, setEmpNo] = useState(employee?.emp_no ?? "");
  const [name, setName] = useState(employee?.name ?? "");
  const [team, setTeam] = useState(employee?.team ?? "");
  const [newConnection, setNewConnection] = useState("");
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
        team: team || null,
        ...(isEdit ? {} : { connection_no: newConnection || null }),
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setSaving(false);
    }
  }

  async function handleAddConnection() {
    if (!employee || !newConnection) return;
    setError(null);
    try {
      await addDialogDataConnection(employee.id, newConnection);
      setNewConnection("");
      onRefresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not add connection");
    }
  }

  async function handleRemoveConnection(connectionId: string) {
    if (!confirm("Remove this connection? It will be excluded from future bill splits.")) return;
    await removeDialogDataConnection(connectionId);
    onRefresh();
  }

  return (
    <div className="panel-overlay" onClick={onCancel}>
      <form className="panel" onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
        <h2>{isEdit ? "Edit Dialog Data Bucket employee" : "Add Dialog Data Bucket employee"}</h2>

        <label>
          EMP No
          <input required value={empNo} onChange={(e) => setEmpNo(e.target.value)} />
        </label>

        <label>
          Name
          <input required value={name} onChange={(e) => setName(e.target.value)} />
        </label>

        <label>
          Team
          <input value={team} onChange={(e) => setTeam(e.target.value)} />
        </label>

        {!isEdit && (
          <label>
            Initial connection no. <span className="field-hint">(optional)</span>
            <input value={newConnection} onChange={(e) => setNewConnection(e.target.value)} />
          </label>
        )}

        {isEdit && employee && (
          <div className="field-group">
            <span className="field-label">Connections</span>
            {employee.connections.length === 0 && <p className="field-hint">No connections yet.</p>}
            {employee.connections.map((c) => (
              <div key={c.id} className="inline-row">
                <span className="mono">{c.connection_no}</span>
                <span className={`pill ${c.status === "active" ? "pill-active" : "pill-resigned"}`}>{c.status}</span>
                <button type="button" className="link-btn link-btn-danger" onClick={() => handleRemoveConnection(c.id)}>
                  Remove
                </button>
              </div>
            ))}
            <div className="inline-row">
              <input
                placeholder="New connection number"
                value={newConnection}
                onChange={(e) => setNewConnection(e.target.value)}
              />
              <button type="button" className="btn btn-ghost" onClick={handleAddConnection} disabled={!newConnection}>
                + Add
              </button>
            </div>
            <p className="field-hint">
              An employee can hold more than one connection — each is billed separately (confirmed against real
              data).
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