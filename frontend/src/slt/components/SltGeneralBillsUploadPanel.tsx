import { useState, type FormEvent } from "react";
import type { SltGeneralImportBatchResult } from "../types/slt";
import { importSltGeneralBills } from "../api/slt";

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

function money(v: string | number | null): string {
  return v == null ? "—" : `Rs. ${Number(v).toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
}

export default function SltGeneralBillsUploadPanel({ onImported, onCancel }: Props) {
  const [month, setMonth] = useState(() => new Date().toISOString().slice(0, 7));
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SltGeneralImportBatchResult | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (files.length === 0) return;
    setError(null);
    setResult(null);
    setUploading(true);
    try {
      const label = monthValueToLabel(month);
      const res = await importSltGeneralBills(label, files);
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
        <h2>Upload SLT general bills</h2>
        <p className="field-hint">
          Select all 4 general account PDFs together — each is processed independently, so one bad file won't
          block the others from importing.
        </p>

        <label>
          Bill month
          <input type="month" required value={month} onChange={(e) => setMonth(e.target.value)} />
        </label>

        <label>
          Bill PDFs <span className="field-hint">(select multiple)</span>
          <input
            type="file"
            accept="application/pdf,.pdf"
            multiple
            required
            onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
          />
          <span className="field-hint">
            {files.length > 0 ? `${files.length} file(s) selected` : "Hold Ctrl/Cmd to select multiple PDFs at once."}
          </span>
        </label>

        {error && <p className="form-error">{error}</p>}

        {result && (
          <div className="field-group">
            <span className="field-label">Import results</span>
            {result.results.map((r) => (
              <div key={r.filename} className="inline-row">
                <span>{r.filename}</span>
                {r.success ? (
                  <span className="pill pill-active">
                    {r.account_label} — {money(r.charges_for_period)}
                  </span>
                ) : (
                  <span className="pill pill-resigned" title={r.error ?? undefined}>
                    Failed: {r.error}
                  </span>
                )}
              </div>
            ))}
          </div>
        )}

        <div className="panel-actions">
          <button type="button" className="btn btn-ghost" onClick={onCancel}>
            {result ? "Close" : "Cancel"}
          </button>
          {!result && (
            <button type="submit" className="btn btn-primary" disabled={uploading || files.length === 0}>
              {uploading ? "Uploading…" : `Import ${files.length || ""} bill${files.length === 1 ? "" : "s"}`}
            </button>
          )}
        </div>
      </form>
    </div>
  );
}