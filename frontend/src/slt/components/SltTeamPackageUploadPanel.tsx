import { useState, type FormEvent } from "react";
import type { SltTeamPackageImportResult } from "../types/slt";
import { importSltTeamPackageBill } from "../api/slt";

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

export default function SltTeamPackageUploadPanel({ onImported, onCancel }: Props) {
  const [month, setMonth] = useState(() => new Date().toISOString().slice(0, 7));
  const [file, setFile] = useState<File | null>(null);
  const [excelFile, setExcelFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SltTeamPackageImportResult | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!file || !excelFile) return;
    setError(null);
    setResult(null);
    setUploading(true);
    try {
      const label = monthValueToLabel(month);
      const res = await importSltTeamPackageBill(label, file, excelFile);
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
        <h2>Upload SLT team package bill</h2>
        <p className="field-hint">
          Both files are required every month — the Excel is uploaded fresh each time and drives that month's
          per-employee package allocation.
        </p>

        <label>
          Bill month
          <input type="month" required value={month} onChange={(e) => setMonth(e.target.value)} />
        </label>

        <label>
          Bill PDF (account 004 767 150X) <span className="field-hint">(required)</span>
          <input type="file" accept="application/pdf,.pdf" required onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
        </label>

        <label>
          Package summary spreadsheet <span className="field-hint">(required)</span>
          <input
            type="file"
            accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            required
            onChange={(e) => setExcelFile(e.target.files?.[0] ?? null)}
          />
          <span className="field-hint">
            This month's spreadsheet listing each employee's package and price — its Summary sheet drives the
            per-employee allocation.
          </span>
        </label>

        {error && <p className="form-error">{error}</p>}

        {result && (
          <div className={`banner ${result.reconciled ? "banner-success" : "banner-error"}`}>
            {result.reconciled ? (
              <>
                ✓ {result.users_count} employees' packages ({money(result.package_sum)}) plus taxes match the
                bill's Total Charges for the Period ({money(result.charges_for_period)}) exactly.
              </>
            ) : (
              <>
                {result.users_count} employees' packages ({money(result.package_sum)}) plus taxes ={" "}
                {money(result.computed_total)}, but the bill states{" "}
                {money(result.charges_for_period)} — off by{" "}
                {money(Math.abs(Number(result.reconciliation_discrepancy)))}. Saved anyway; worth a quick review.
              </>
            )}
          </div>
        )}

        <div className="panel-actions">
          <button type="button" className="btn btn-ghost" onClick={onCancel}>
            {result ? "Close" : "Cancel"}
          </button>
          {!result && (
            <button type="submit" className="btn btn-primary" disabled={uploading || !file || !excelFile}>
              {uploading ? "Uploading…" : "Import bill"}
            </button>
          )}
        </div>
      </form>
    </div>
  );
}