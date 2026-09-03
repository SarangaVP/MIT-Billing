import { useState, type FormEvent } from "react";
import type { DialogMobileImportResult } from "../types/dialogMobile";
import { importDialogMobileBillPdf } from "../api/dialogMobile";

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

export default function DialogMobileBillUploadPanel({ onImported, onCancel }: Props) {
  const [month, setMonth] = useState(() => new Date().toISOString().slice(0, 7));
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DialogMobileImportResult | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!file) return;
    setError(null);
    setResult(null);
    setUploading(true);
    try {
      const label = monthValueToLabel(month);
      const res = await importDialogMobileBillPdf(label, file);
      setResult(res);
      // The backend always saves the import now — a reconciliation mismatch
      // (PDF or .xls) is recorded and shown as "Off by Rs. X" rather than
      // blocking the save, so this always proceeds to refresh the list.
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
            ) : (
              <>
                Imported {result.line_items_imported} lines from the {result.source_format.toUpperCase()} file.
                Parsed total {money(result.parsed_total_charges_for_bill_period)} is off by{" "}
                {money(Math.abs(Number(result.reconciliation_discrepancy ?? 0)))} from the invoice's stated total{" "}
                {result.stated_total_charges_for_bill_period != null
                  ? money(result.stated_total_charges_for_bill_period)
                  : ""}
                . The bill was still saved — review the discrepancy on the Bills page.
              </>
            )}
          </div>
        )}

        {result && (result.data_bucket_auto_selected || result.auto_bucket_excluded_mobile_nos.length > 0) && (
          <div className="banner banner-success">
            {result.data_bucket_auto_selected && (
              <div>✓ Data bucket number 765155535 was found and selected automatically for this bill.</div>
            )}
            {result.auto_bucket_excluded_mobile_nos.length > 0 && (
              <div style={{ marginTop: result.data_bucket_auto_selected ? 6 : 0 }}>
                ✓ {result.auto_bucket_excluded_mobile_nos.length} connection
                {result.auto_bucket_excluded_mobile_nos.length > 1 ? "s were" : " was"} automatically excluded from
                the bucket: {result.auto_bucket_excluded_mobile_nos.join(", ")}. Adjustable anytime via "Manage
                bucket exclusion".
              </div>
            )}
          </div>
        )}

        {result && result.corrupted_value_warnings.length > 0 && (
          <div className="banner banner-error">
            {result.corrupted_value_warnings.length} value{result.corrupted_value_warnings.length > 1 ? "s" : ""} in
            the source file were too large to store (likely a broken formula in Dialog's own export) and{" "}
            {result.corrupted_value_warnings.length > 1 ? "were" : "was"} reset to 0 so the import could still
            complete. The connection{result.corrupted_value_warnings.length > 1 ? "s were" : " was"} still imported —
            check and correct manually via "Edit line item" if needed:
            <ul style={{ margin: "8px 0 0", paddingLeft: 18 }}>
              {result.corrupted_value_warnings.map((w, i) => (
                <li key={i}>{w}</li>
              ))}
            </ul>
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