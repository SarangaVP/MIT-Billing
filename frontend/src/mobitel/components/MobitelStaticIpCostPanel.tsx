import { useState, type FormEvent } from "react";
import type { MobitelBillLineItemOut } from "../types/mobitel";

interface Props {
  row: MobitelBillLineItemOut;
  onSave: (cost: string) => Promise<void>;
  onCancel: () => void;
}

export default function MobitelStaticIpCostPanel({ row, onSave, onCancel }: Props) {
  const [cost, setCost] = useState(row.static_ip_cost);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const displayName = row.name || "this employee";

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      await onSave(cost || "0");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="panel-overlay" onClick={onCancel}>
      <form className="panel panel-small" onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
        <h2>Set static IP cost</h2>
        <p className="field-hint">
          For <strong>{displayName}</strong>, this bill only. Changing this recalculates the data cost split for
          every employee in this bill period, not just {displayName.split(" ")[0]}.
        </p>

        <label>
          Cost (Rs.)
          <input
            type="number"
            step="0.01"
            min="0"
            autoFocus
            value={cost}
            onChange={(e) => setCost(e.target.value)}
          />
        </label>

        {error && <p className="form-error">{error}</p>}

        <div className="panel-actions">
          <button type="button" className="btn btn-ghost" onClick={onCancel}>
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? "Saving…" : "Save & recalculate"}
          </button>
        </div>
      </form>
    </div>
  );
}