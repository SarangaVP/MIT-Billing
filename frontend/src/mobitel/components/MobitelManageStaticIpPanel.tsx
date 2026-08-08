import { useState, type FormEvent } from "react";
import type { MobitelBillLineItemOut } from "../types/mobitel";
import MobitelConfirmPanel from "./MobitelConfirmPanel";

interface Props {
  rows: MobitelBillLineItemOut[];
  onSave: (lineItemId: string, cost: string) => Promise<void>;
  onCancel: () => void;
}

export default function MobitelManageStaticIpPanel({ rows, onSave, onCancel }: Props) {
  const currentHolders = rows.filter((r) => Number(r.static_ip_cost) > 0);

  const [selectedId, setSelectedId] = useState("");
  const [cost, setCost] = useState("1500");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [removingRow, setRemovingRow] = useState<MobitelBillLineItemOut | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!selectedId) return;
    setError(null);
    setSaving(true);
    try {
      await onSave(selectedId, cost || "0");
      setSelectedId("");
      setCost("1500");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save");
    } finally {
      setSaving(false);
    }
  }

  async function handleConfirmRemove() {
    if (!removingRow) return;
    await onSave(removingRow.id, "0");
    setRemovingRow(null);
  }

  return (
    <div className="panel-overlay" onClick={onCancel}>
      <form className="panel" onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
        <h2>Manage static IP costs</h2>
        <p className="field-hint">
          Static IP is a rare per-employee add-on — normally only one or two people have it. Changing any value
          here recalculates the data cost split for everyone in this bill.
        </p>

        {currentHolders.length > 0 && (
          <div className="field-group">
            <span className="field-label">Currently set</span>
            {currentHolders.map((row) => (
              <div key={row.id} className="inline-row">
                <span>{row.name}</span>
                <span className="mono">Rs. {Number(row.static_ip_cost).toLocaleString()}</span>
                <button type="button" className="link-btn" onClick={() => setSelectedId(row.id)}>
                  Edit
                </button>
                <button type="button" className="link-btn link-btn-danger" onClick={() => setRemovingRow(row)}>
                  Remove
                </button>
              </div>
            ))}
          </div>
        )}

        {currentHolders.length === 0 && (
          <p className="field-hint">No one currently has a static IP cost set for this bill.</p>
        )}

        <label>
          Employee
          <select required value={selectedId} onChange={(e) => setSelectedId(e.target.value)}>
            <option value="" disabled>
              Select employee…
            </option>
            {rows.map((row) => (
              <option key={row.id} value={row.id}>
                {row.name} ({row.emp_no}){Number(row.static_ip_cost) > 0 ? " — currently set" : ""}
              </option>
            ))}
          </select>
        </label>

        <label>
          Cost (Rs.)
          <input type="number" step="0.01" min="0" value={cost} onChange={(e) => setCost(e.target.value)} />
        </label>

        {error && <p className="form-error">{error}</p>}

        <div className="panel-actions">
          <button type="button" className="btn btn-ghost" onClick={onCancel}>
            Close
          </button>
          <button type="submit" className="btn btn-primary" disabled={saving || !selectedId}>
            {saving ? "Saving…" : "Save & recalculate"}
          </button>
        </div>
      </form>

      {removingRow && (
        <MobitelConfirmPanel
          title="Remove static IP cost?"
          message={`This removes ${removingRow.name}'s static IP cost and recalculates the data cost split for everyone in this bill.`}
          onConfirm={handleConfirmRemove}
          onCancel={() => setRemovingRow(null)}
        />
      )}
    </div>
  );
}