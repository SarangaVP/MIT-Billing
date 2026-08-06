import { useState, type FormEvent } from "react";
import type { MobitelImportResult } from "../types/mobitel";
import { importMobitelBill } from "../api/mobitel";

interface Props {
  onImported: () => void;
  onCancel: () => void;
}

const MONTH_NAMES = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

function monthValueToLabel(monthValue: string): string {
  const [year, month] = monthValue.split("-");
  const idx = parseInt(month, 10) - 1;
  return `${MONTH_NAMES[idx]} ${year}`;
}

function money(v: string | number): string {
  return `Rs. ${Number(v).toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
}

export default function MobitelBillUploadPanel({ onImported, onCancel }: Props) {
  const [month, setMonth] = useState(() => new Date().toISOString().slice(0, 7));
  const [file, setFile] = useState<File | null>(null);
  const [portalFile, setPortalFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<MobitelImportResult | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!file) return;
    setError(null);
    setResult(null);
    setUploading(true);
    try {
      const label = monthValueToLabel(month);
      const res = await importMobitelBill(label, file, portalFile);
      setResult(res);
      onImported();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="panel-overlay" onClick={onCancel}>
      <form className="panel" onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
        <h2>Upload Mobitel bill</h2>

        <label>
          Bill month
          <input type="month" required value={month} onChange={(e) => setMonth(e.target.value)} />
        </label>

        <label>
          Bill PDF <span className="field-hint">(required)</span>
          <input type="file" accept="application/pdf,.pdf" required onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
          <span className="field-hint">
            The Mobitel corporate tax invoice PDF. Costs are split across currently active employees automatically.
          </span>
        </label>

        <label>
          Portal sheet <span className="field-hint">(optional)</span>
          <input
            type="file"
            accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            onChange={(e) => setPortalFile(e.target.files?.[0] ?? null)}
          />
          <span className="field-hint">
            The Mobitel "Portal" export (.xlsx) — adds per-SIM usage detail (data volume, daily limit, member status)
            to this month's summary. Skip if you only want the cost split.
          </span>
        </label>

        {error && <p className="form-error">{error}</p>}

        {result && (
          <div className={`banner ${result.reconciled ? "banner-success" : "banner-error"}`}>
            {result.reconciled ? (
              <>
                ✓ Split {money(result.net)} across {result.users_count} employees (
                {money(result.per_user_cost)} each). Matches exactly.
              </>
            ) : (
              <>
                Split {money(result.net)} across {result.users_count} employees. Line items sum to{" "}
                {money(result.parsed_total)} — off by {money(Math.abs(Number(result.reconciliation_discrepancy)))}{" "}
                from Net (small rounding drift is expected when splitting evenly).
              </>
            )}
          </div>
        )}

        <div className="panel-actions">
          <button type="button" className="btn btn-ghost" onClick={onCancel}>
            {result ? "Close" : "Cancel"}
          </button>
          {!result && (
            <button type="submit" className="btn btn-primary" disabled={uploading || !file}>
              {uploading ? "Uploading…" : "Import bill"}
            </button>
          )}
        </div>
      </form>
    </div>
  );
}