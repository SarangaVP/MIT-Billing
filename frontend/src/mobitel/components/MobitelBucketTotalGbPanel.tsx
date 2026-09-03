import { useState, type FormEvent } from "react";

interface Props {
  periodLabel: string;
  currentBucketTotalGb: string;
  onSave: (bucketTotalGb: string) => Promise<void>;
  onCancel: () => void;
}

export default function MobitelBucketTotalGbPanel({ periodLabel, currentBucketTotalGb, onSave, onCancel }: Props) {
  const [value, setValue] = useState(currentBucketTotalGb);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      await onSave(value);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="panel-overlay" onClick={onCancel}>
      <form className="panel panel-small" onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
        <h2>Set bucket total GB for {periodLabel}</h2>
        <p className="field-hint">
          Used as the divisor for automatic project cost calculations this month (price per GB = Net ÷ this
          value). Defaults to 4000, but the plan's contracted size can genuinely change between months — update
          it here if this bill's real bucket size is different. Saving recalculates every auto-eligible project
          cost, plus the equal split for everyone else.
        </p>

        <label>
          Bucket total (GB)
          <input type="number" step="1" min="1" required value={value} onChange={(e) => setValue(e.target.value)} />
        </label>

        {error && <p className="form-error">{error}</p>}

        <div className="panel-actions">
          <button type="button" className="btn btn-ghost" onClick={onCancel}>
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={saving || !value}>
            {saving ? "Saving…" : "Save & recalculate"}
          </button>
        </div>
      </form>
    </div>
  );
}