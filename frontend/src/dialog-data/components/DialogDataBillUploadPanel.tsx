import { useState, type FormEvent } from "react";
import type { DialogDataImportResult } from "../types/dialogData";
import { importDialogDataBill } from "../api/dialogData";

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

export default function DialogDataBillUploadPanel({ onImported, onCancel }: Props) {
  const [month, setMonth] = useState(() => new Date().toISOString().slice(0, 7));
  const [file, setFile] = useState<File | null>(null);
  const [billSheetFile, setBillSheetFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DialogDataImportResult | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!file) return;
    setError(null);
    setResult(null);
    setUploading(true);
    try {
      const label = monthValueToLabel(month);
      const res = await importDialogDataBill(label, file, billSheetFile);
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
        <h2>Upload Dialog Data Bucket bill</h2>

        <label>
          Bill month
          <input type="month" required value={month} onChange={(e) => setMonth(e.target.value)} />
        </label>

        <label>
          Bill PDF <span className="field-hint">(required)</span>
          <input type="file" accept="application/pdf,.pdf" required onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
          <span className="field-hint">
            The Dialog master account tax invoice PDF. Costs are split across currently active connections
            automatically.
          </span>
        </label>

        <label>
          Bill sheet <span className="field-hint">(optional)</span>
          <input
            type="file"
            accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            onChange={(e) => setBillSheetFile(e.target.files?.[0] ?? null)}
          />
          <span className="field-hint">
            The Dialog "Bill" sheet export (.xlsx) — adds per-connection usage detail (Allocation/Usage/Remaining
            GB) to this month's summary. Skip if you only want the cost split.
          </span>
        </label>

        {error && <p className="form-error">{error}</p>}

        {result && (
          <>
            <div className={`banner ${result.reconciled ? "banner-success" : "banner-error"}`}>
              {result.reconciled ? (
                <>
                  ✓ Split {money(result.net)} across {result.users_count} connections (
                  {money(result.per_user_cost)} each). Matches exactly.
                </>
              ) : (
                <>
                  Split {money(result.net)} across {result.users_count} connections. Line items sum to{" "}
                  {money(result.parsed_total)} — off by {money(Math.abs(Number(result.reconciliation_discrepancy)))}{" "}
                  from Net (small rounding drift is expected when splitting evenly).
                </>
              )}
            </div>
            {result.unmatched_in_bill_sheet.length > 0 && (
              <div className="banner banner-error">
                Dialog billed {result.unmatched_in_bill_sheet.length} connection
                {result.unmatched_in_bill_sheet.length > 1 ? "s" : ""} not in your employee list, so{" "}
                {result.unmatched_in_bill_sheet.length > 1 ? "they were" : "it was"} excluded from the split:{" "}
                {result.unmatched_in_bill_sheet.join(", ")}. Add {result.unmatched_in_bill_sheet.length > 1 ? "them" : "it"}{" "}
                as an employee if this connection belongs to someone.
              </div>
            )}
          </>
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