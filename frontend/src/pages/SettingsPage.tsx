import { useEffect, useState, useCallback, type FormEvent } from "react";
import type { BucketRate } from "../types/bucketRate";
import { listBucketRates, createBucketRate } from "../api/bucketRates";

const KNOWN_DEFAULT_COST = "590.39";
const KNOWN_DEFAULT_VAT = "90.06";

export default function SettingsPage() {
  const [rates, setRates] = useState<BucketRate[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);

  const [cost, setCost] = useState(KNOWN_DEFAULT_COST);
  const [vat, setVat] = useState(KNOWN_DEFAULT_VAT);
  const [effectiveFrom, setEffectiveFrom] = useState(() => new Date().toISOString().slice(0, 10));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listBucketRates();
      setRates(data);
      const active = data.find((r) => new Date(r.effective_from) <= new Date());
      if (active) {
        setCost(String(active.cost));
        setVat(String(active.vat));
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const today = new Date();
  const activeRate = rates.find((r) => new Date(r.effective_from) <= today);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      await createBucketRate({ cost: Number(cost), vat: Number(vat), effective_from: effectiveFrom });
      setShowForm(false);
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
          <h1>Settings</h1>
          <p className="page-subtitle">
            The flat monthly plan rate applied per line ("Bucket cost") — a fixed company rate, not taken from any
            bill.
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowForm(true)}>
          + Change rate
        </button>
      </div>

      {loading && <p className="field-hint">Loading…</p>}

      {!loading && !activeRate && (
        <div className="banner banner-error">
          No bucket rate has been set yet. Bill summaries will show Rs. 0 for Bucket cost until one is added — the
          known default is Rs. {KNOWN_DEFAULT_COST} cost / Rs. {KNOWN_DEFAULT_VAT} VAT.
        </div>
      )}

      {!loading && activeRate && (
        <div className="table-wrap" style={{ padding: 20, marginBottom: 20 }}>
          <p className="field-hint" style={{ marginBottom: 10 }}>
            Currently active (effective from {activeRate.effective_from})
          </p>
          <div style={{ display: "flex", gap: 32 }}>
            <div>
              <div className="page-subtitle">Bucket cost</div>
              <div className="mono" style={{ fontSize: "1.3rem" }}>
                Rs. {Number(activeRate.cost).toLocaleString()}
              </div>
            </div>
            <div>
              <div className="page-subtitle">Bucket VAT</div>
              <div className="mono" style={{ fontSize: "1.3rem" }}>
                Rs. {Number(activeRate.vat).toLocaleString()}
              </div>
            </div>
            <div>
              <div className="page-subtitle">Bucket Nett</div>
              <div className="mono" style={{ fontSize: "1.3rem" }}>
                Rs. {(Number(activeRate.cost) - Number(activeRate.vat)).toLocaleString()}
              </div>
            </div>
          </div>
        </div>
      )}

      {!loading && rates.length > 0 && (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Effective from</th>
                <th>Cost</th>
                <th>VAT</th>
                <th>Nett</th>
              </tr>
            </thead>
            <tbody>
              {rates.map((r) => (
                <tr key={r.id}>
                  <td className="mono">{r.effective_from}</td>
                  <td className="mono">Rs. {Number(r.cost).toLocaleString()}</td>
                  <td className="mono">Rs. {Number(r.vat).toLocaleString()}</td>
                  <td className="mono">Rs. {(Number(r.cost) - Number(r.vat)).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showForm && (
        <div className="panel-overlay" onClick={() => setShowForm(false)}>
          <form className="panel panel-small" onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
            <h2>Set a new bucket rate</h2>
            <p className="field-hint">
              This adds a new rate effective from the date below — past bill periods keep using whatever rate was
              active at the time, so history never changes retroactively.
            </p>

            <label>
              Cost (Rs.)
              <input type="number" step="0.01" required value={cost} onChange={(e) => setCost(e.target.value)} />
            </label>
            <label>
              VAT (Rs.)
              <input type="number" step="0.01" required value={vat} onChange={(e) => setVat(e.target.value)} />
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