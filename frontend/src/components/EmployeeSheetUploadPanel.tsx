import { useState, type FormEvent } from "react";

interface SyncResult {
  inserted_employees: number;
  updated_employees: number;
  revived_employees: number;
  retired_employees: number;
  skipped_missing_rows: number;
  conflicts: string[];
  [key: string]: unknown;   // covers module-specific fields (numbers_added vs connections_added, etc.)
}

interface Props {
  title: string;
  uploadFn: (file: File) => Promise<SyncResult>;
  onImported: () => void;
  onCancel: () => void;
}

/** Shared across all 3 modules — Dialog Mobile, Mobitel, Dialog Data Bucket
 * all report the same result shape, just with different extra fields. */
export default function EmployeeSheetUploadPanel({ title, uploadFn, onImported, onCancel }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SyncResult | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!file) return;
    setError(null);
    setResult(null);
    setUploading(true);
    try {
      const res = await uploadFn(file);
      setResult(res);
      onImported();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  const connectionsAddedKey = ["connections_added", "numbers_added"].find((k) => result && k in result);
  const connectionsRetiredKey = ["connections_retired", "numbers_retired"].find((k) => result && k in result);
  const connectionsReactivatedKey = ["connections_reactivated", "numbers_reactivated"].find((k) => result && k in result);

  return (
    <div className="panel-overlay" onClick={onCancel}>
      <form className="panel" onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
        <h2>{title}</h2>
        <p className="field-hint">
          This sheet is treated as the full, current roster — anyone already in the system gets their details
          refreshed to match it, anyone missing from it is retired (not deleted — their billing history stays
          intact), and anyone new is added.
        </p>

        <label>
          Employee sheet (.xlsx) <span className="field-hint">(required)</span>
          <input
            type="file"
            accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            required
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
        </label>

        {error && <p className="form-error">{error}</p>}

        {result && (
          <div className="field-group">
            <span className="field-label">Result</span>
            <div className="inline-row">
              <span>New employees</span>
              <span className="mono">{result.inserted_employees}</span>
            </div>
            <div className="inline-row">
              <span>Updated employees</span>
              <span className="mono">{result.updated_employees}</span>
            </div>
            {result.revived_employees > 0 && (
              <div className="inline-row">
                <span>Revived (previously retired)</span>
                <span className="mono">{result.revived_employees}</span>
              </div>
            )}
            {result.retired_employees > 0 && (
              <div className="inline-row">
                <span>Retired (missing from this sheet)</span>
                <span className="mono">{result.retired_employees}</span>
              </div>
            )}
            {connectionsAddedKey && (
              <div className="inline-row">
                <span>Numbers added</span>
                <span className="mono">{result[connectionsAddedKey] as number}</span>
              </div>
            )}
            {connectionsRetiredKey && (result[connectionsRetiredKey] as number) > 0 && (
              <div className="inline-row">
                <span>Numbers retired</span>
                <span className="mono">{result[connectionsRetiredKey] as number}</span>
              </div>
            )}
            {connectionsReactivatedKey && (result[connectionsReactivatedKey] as number) > 0 && (
              <div className="inline-row">
                <span>Numbers reactivated</span>
                <span className="mono">{result[connectionsReactivatedKey] as number}</span>
              </div>
            )}
            {result.skipped_missing_rows > 0 && (
              <div className="inline-row">
                <span>Skipped (blank rows)</span>
                <span className="mono">{result.skipped_missing_rows}</span>
              </div>
            )}
          </div>
        )}

        {result && result.conflicts.length > 0 && (
          <div className="banner banner-error">
            {result.conflicts.length} conflict{result.conflicts.length > 1 ? "s" : ""} — these were NOT applied
            automatically, since a number/connection appears to belong to someone else already:
            <ul style={{ margin: "8px 0 0", paddingLeft: 18 }}>
              {result.conflicts.map((c, i) => (
                <li key={i}>{c}</li>
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
              {uploading ? "Uploading…" : "Sync roster"}
            </button>
          )}
        </div>
      </form>
    </div>
  );
}