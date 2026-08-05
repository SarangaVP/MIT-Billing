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

export default function BillUploadPanel({ onImported, onCancel }: Props) {
  const [month, setMonth] = useState(() => new Date().toISOString().slice(0, 7)); // "YYYY-MM"
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
      if (res.reconciled) {
        onImported();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="panel-overlay" onClick={onCancel}>
      <form className="panel" onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
        <h2>Upload monthly bill</h2>

        <label>
          Bill month
          <input type="month" required value={month} onChange={(e) => setMonth(e.target.value)} />
        </label>

        <label>
          Bill PDF
          <input
            type="file"
            accept="application/pdf"
            required
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
          <span className="field-hint">The full Dialog corporate bill PDF for this month.</span>
        </label>

        {error && <p className="form-error">{error}</p>}

        {result && (
          <div className={`banner ${result.reconciled ? "banner-success" : "banner-error"}`}>
            {result.reconciled ? (
              <>
                ✓ Imported {result.line_items_imported} lines. Parsed total{" "}
                <strong>Rs. {Number(result.parsed_total_charges_for_bill_period).toLocaleString()}</strong> matches
                the invoice exactly.
              </>
            ) : (
              <>
                Reconciliation failed — parsed total{" "}
                {Number(result.parsed_total_charges_for_bill_period).toLocaleString()} does not match the invoice's
                stated total {Number(result.stated_total_charges_for_bill_period ?? 0).toLocaleString()}. Nothing was
                saved.
              </>
            )}
          </div>
        )}

        <div className="panel-actions">
          <button type="button" className="btn btn-ghost" onClick={onCancel}>
            {result?.reconciled ? "Close" : "Cancel"}
          </button>
          {!result?.reconciled && (
            <button type="submit" className="btn btn-primary" disabled={uploading || !file}>
              {uploading ? "Uploading…" : "Import bill"}
            </button>
          )}
        </div>
      </form>
    </div>
  );
}