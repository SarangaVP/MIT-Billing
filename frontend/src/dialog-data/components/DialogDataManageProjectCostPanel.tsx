import { useState, type FormEvent } from "react";
import type { DialogDataBillLineItemOut } from "../types/dialogData";
import DialogDataConfirmPanel from "./DialogDataConfirmPanel";

interface Props {
  rows: DialogDataBillLineItemOut[];
  onSave: (lineItemId: string, isProjectCost: boolean, amount: string | null) => Promise<void>;
  onCancel: () => void;
}

export default function DialogDataManageProjectCostPanel({ rows, onSave, onCancel }: Props) {
  const currentHolders = rows.filter((r) => r.is_project_cost);

  const [selectedId, setSelectedId] = useState("");
  const [amount, setAmount] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [removingRow, setRemovingRow] = useState<DialogDataBillLineItemOut | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!selectedId || !amount) return;
    setError(null);
    setSaving(true);
    try {
      await onSave(selectedId, true, amount);
      setSelectedId("");
      setAmount("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save");
    } finally {
      setSaving(false);
    }
  }

  async function handleConfirmRemove() {
    if (!removingRow) return;
    await onSave(removingRow.id, false, null);
    setRemovingRow(null);
  }

  return (
    <div className="panel-overlay" onClick={onCancel}>
      <form className="panel" onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
        <h2>Manage project costs</h2>
        <p className="field-hint">
          Use this when someone's real charge for the month is a specific known amount rather than an equal
          share — that person is excluded from both the shared total and the headcount, so everyone else's
          split adjusts automatically. Rare — normally zero or one person per bill.
        </p>

        {currentHolders.length > 0 && (
          <div className="field-group">
            <span className="field-label">Currently set</span>
            {currentHolders.map((row) => (
              <div key={row.id} className="inline-row">
                <span>{row.name}</span>
                <span className="mono">Rs. {Number(row.project_cost_amount ?? 0).toLocaleString()}</span>
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
          <p className="field-hint">No one currently has a project cost set for this bill.</p>
        )}

        <label>
          Employee
          <select required value={selectedId} onChange={(e) => setSelectedId(e.target.value)}>
            <option value="" disabled>
              Select employee…
            </option>
            {rows.map((row) => (
              <option key={row.id} value={row.id}>
                {row.name} ({row.emp_no}){row.is_project_cost ? " — currently set" : ""}
              </option>
            ))}
          </select>
        </label>

        <label>
          Project cost (Rs.)
          <input type="number" step="0.01" min="0" required value={amount} onChange={(e) => setAmount(e.target.value)} />
        </label>

        {error && <p className="form-error">{error}</p>}

        <div className="panel-actions">
          <button type="button" className="btn btn-ghost" onClick={onCancel}>
            Close
          </button>
          <button type="submit" className="btn btn-primary" disabled={saving || !selectedId || !amount}>
            {saving ? "Saving…" : "Save & recalculate"}
          </button>
        </div>
      </form>

      {removingRow && (
        <DialogDataConfirmPanel
          title="Remove project cost?"
          message={`This removes ${removingRow.name}'s project cost — they'll go back to the equal split, and everyone else's cost recalculates too.`}
          onConfirm={handleConfirmRemove}
          onCancel={() => setRemovingRow(null)}
        />
      )}
    </div>
  );
}