import { useState, type FormEvent } from "react";

interface Props {
  periodLabel: string;
  currentOverrideCost: string | null;
  currentOverrideVat: string | null;
  onSave: (cost: number | null, vat: number | null) => Promise<void>;
  onCancel: () => void;
}

export default function BucketRatePanel({
  periodLabel,
  currentOverrideCost,
  currentOverrideVat,
  onSave,
  onCancel,
}: Props) {
  const hasOverride = currentOverrideCost !== null || currentOverrideVat !== null;

  const [cost, setCost] = useState(currentOverrideCost ?? "0");
  const [vat, setVat] = useState(currentOverrideVat ?? "0");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      await onSave(Number(cost), Number(vat));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save");
    } finally {
      setSaving(false);
    }
  }

  async function handleClear() {
    setError(null);
    setSaving(true);
    try {
      await onSave(null, null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not clear");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="panel-overlay" onClick={onCancel}>
      <form className="panel panel-small" onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
        <h2>Set bucket rate for {periodLabel}</h2>
        <p className="field-hint">
          There's no standard/default rate anymore — every bill period needs its own bucket cost/VAT set
          explicitly here. Until it's set, bucket cost is Rs. 0 for this month. This only affects{" "}
          <strong>{periodLabel}</strong> — no other bill period is touched.
        </p>

        {!hasOverride && (
          <p className="field-hint">
            <strong>No rate set yet for this month</strong> — bucket cost is currently Rs. 0 for every line item.
          </p>
        )}

        <label>
          Cost (Rs.)
          <input type="number" step="0.01" required value={cost} onChange={(e) => setCost(e.target.value)} />
        </label>
        <label>
          VAT (Rs.)
          <input type="number" step="0.01" required value={vat} onChange={(e) => setVat(e.target.value)} />
        </label>

        {error && <p className="form-error">{error}</p>}

        <div className="panel-actions">
          {hasOverride && (
            <button type="button" className="btn btn-ghost" onClick={handleClear} disabled={saving}>
              Clear (reset to Rs. 0)
            </button>
          )}
          <button type="button" className="btn btn-ghost" onClick={onCancel}>
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? "Saving…" : "Save for this month"}
          </button>
        </div>
      </form>
    </div>
  );
}