import { useState, type FormEvent } from "react";
import type { ImportResult } from "../types/bill";
import { importBillPdf } from "../api/bills";

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

export default function BillUploadPanel({ onImported, onCancel }: Props) {
  const [month, setMonth] = useState(() => new Date().toISOString().slice(0, 7));
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ImportResult | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!file) return;
    setError(null);
    setResult(null);
    setUploading(true);
    try {
      const label = monthValueToLabel(month);
      const res = await importBillPdf(label, file);
      setResult(res);
      if (res.reconciled || res.source_format === "xls") {
        // .xls imports succeed even with the known dormant-account gap —
        // only a genuinely failed PDF import should block moving on.
        onImported();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  const isBlockingFailure = result && !result.reconciled && result.source_format === "pdf";

  return (
    <div className="panel-overlay" onClick={onCancel}>
      <form className="panel" onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
        <h2>Upload monthly bill</h2>

        <label>
          Bill month
          <input type="month" required value={month} onChange={(e) => setMonth(e.target.value)} />
        </label>

        <label>
          Bill file
          <input
            type="file"
            accept="application/pdf,.pdf,.xls,application/vnd.ms-excel"
            required
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
          <span className="field-hint">
            Either the full Dialog PDF invoice, or the .xls export — both are supported.
          </span>
        </label>

        {error && <p className="form-error">{error}</p>}

        {result && (
          <div className={`banner ${result.reconciled ? "banner-success" : "banner-error"}`}>
            {result.reconciled ? (
              <>
                ✓ Imported {result.line_items_imported} lines from a {result.source_format.toUpperCase()} file.
                Parsed total <strong>{money(result.parsed_total_charges_for_bill_period)}</strong> matches the
                invoice exactly.
              </>
            ) : result.source_format === "xls" ? (
              <>
                Imported {result.line_items_imported} lines from the .xls file. Parsed total{" "}
                {money(result.parsed_total_charges_for_bill_period)} is off by{" "}
                {money(Math.abs(Number(result.reconciliation_discrepancy ?? 0)))} from the invoice's stated total — this is
                expected (the .xls export omits some dormant/zero-activity accounts) and was allowed.
              </>
            ) : (
              <>
                Reconciliation failed — parsed total {money(result.parsed_total_charges_for_bill_period)} does not
                match the invoice's stated total{" "}
                {money(result.stated_total_charges_for_bill_period ?? 0)}. Nothing was saved.
              </>
            )}
          </div>
        )}

        <div className="panel-actions">
          <button type="button" className="btn btn-ghost" onClick={onCancel}>
            {result && !isBlockingFailure ? "Close" : "Cancel"}
          </button>
          {!(result && !isBlockingFailure) && (
            <button type="submit" className="btn btn-primary" disabled={uploading || !file}>
              {uploading ? "Uploading…" : "Import bill"}
            </button>
          )}
        </div>
      </form>
    </div>
  );
}