import { useState, type FormEvent } from "react";
import type { DialogMobileBillSummaryRow } from "../types/dialogMobile";
import DialogMobileConfirmPanel from "./DialogMobileConfirmPanel";

interface Props {
  rows: DialogMobileBillSummaryRow[];
  onSave: (lineItemId: string, isBucketExcluded: boolean) => Promise<void>;
  onCancel: () => void;
}

export default function DialogMobileBucketExclusionPanel({ rows, onSave, onCancel }: Props) {
  const currentlyExcluded = rows.filter((r) => r.is_bucket_excluded);

  const [selectedId, setSelectedId] = useState("");
  const [search, setSearch] = useState("");
  const [showResults, setShowResults] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [removingRow, setRemovingRow] = useState<DialogMobileBillSummaryRow | null>(null);

  const selectedRow = rows.find((r) => r.bill_line_item_id === selectedId) || null;

  const pattern = search.trim().toLowerCase();
  const filteredRows = pattern
    ? rows.filter(
        (r) =>
          (r.name ?? "").toLowerCase().includes(pattern) ||
          (r.emp_no ?? "").toLowerCase().includes(pattern) ||
          (r.project_label ?? "").toLowerCase().includes(pattern) ||
          r.mobile_no.includes(pattern)
      )
    : rows;

  function handlePickRow(row: DialogMobileBillSummaryRow) {
    setSelectedId(row.bill_line_item_id);
    setSearch(`${row.name} (${row.emp_no})`);
    setShowResults(false);
  }

  function handleSearchChange(value: string) {
    setSearch(value);
    setShowResults(true);
    if (selectedId) setSelectedId(""); // typing again clears any previous pick
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!selectedId) return;
    setError(null);
    setSaving(true);
    try {
      await onSave(selectedId, true);
      setSelectedId("");
      setSearch("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save");
    } finally {
      setSaving(false);
    }
  }

  async function handleConfirmRemove() {
    if (!removingRow) return;
    await onSave(removingRow.bill_line_item_id, false);
    setRemovingRow(null);
  }

  return (
    <div className="panel-overlay" onClick={onCancel}>
      <form className="panel" onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
        <h2>Manage bucket exclusion</h2>
        <p className="field-hint">
          Use this to exclude a connection from the bucket allocation for THIS bill period specifically —
          typically for General lines (e.g. Security, Driver, Data bucket), though any connection can be
          picked. Doesn't affect anyone else's total; disconnected-this-month and Intern connections are
          still excluded automatically and don't need to be added here.
        </p>

        {currentlyExcluded.length > 0 && (
          <div className="field-group">
            <span className="field-label">Currently excluded</span>
            {currentlyExcluded.map((row) => (
              <div key={row.bill_line_item_id} className="inline-row">
                <span>{row.name}</span>
                {row.project_label && <span className="pill pill-transferred">{row.project_label}</span>}
                <button type="button" className="link-btn link-btn-danger" onClick={() => setRemovingRow(row)}>
                  Remove
                </button>
              </div>
            ))}
          </div>
        )}

        {currentlyExcluded.length === 0 && (
          <p className="field-hint">No one is currently excluded from the bucket for this bill.</p>
        )}

        <label>
          Employee
          <div style={{ position: "relative" }}>
            <input
              type="text"
              className="search-input"
              placeholder="Search by name, EMP No, or mobile no…"
              value={search}
              onChange={(e) => handleSearchChange(e.target.value)}
              onFocus={() => setShowResults(true)}
              onBlur={() => setTimeout(() => setShowResults(false), 100)}
              autoComplete="off"
            />

            {showResults && (
              <div
                style={{
                  position: "absolute",
                  top: "calc(100% + 4px)",
                  left: 0,
                  right: 0,
                  maxHeight: 220,
                  overflowY: "auto",
                  background: "var(--surface)",
                  border: "1px solid var(--border)",
                  borderRadius: 10,
                  zIndex: 10,
                }}
              >
                {filteredRows.length === 0 && <div className="field-hint" style={{ padding: "8px 12px" }}>No matches.</div>}
                {filteredRows.map((row) => (
                  <div
                    key={row.bill_line_item_id}
                    className="inline-row"
                    style={{ padding: "8px 12px", cursor: "pointer" }}
                    onMouseDown={() => handlePickRow(row)}
                  >
                    <span>
                      {row.name} <span className="mono muted">({row.emp_no})</span>
                    </span>
                    <div style={{ display: "flex", gap: 4, marginLeft: "auto" }}>
                      {row.project_label && <span className="pill pill-transferred">{row.project_label}</span>}
                      {row.is_bucket_excluded && <span className="pill pill-transferred">Excluded</span>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </label>

        {error && <p className="form-error">{error}</p>}

        <div className="panel-actions">
          <button type="button" className="btn btn-ghost" onClick={onCancel}>
            Close
          </button>
          <button type="submit" className="btn btn-primary" disabled={saving || !selectedRow}>
            {saving ? "Saving…" : "Add to excluded"}
          </button>
        </div>
      </form>

      {removingRow && (
        <DialogMobileConfirmPanel
          title="Remove bucket exclusion?"
          message={`This puts ${removingRow.name} back into the standard bucket allocation for this bill period.`}
          confirmLabel="Remove"
          onConfirm={handleConfirmRemove}
          onCancel={() => setRemovingRow(null)}
        />
      )}
    </div>
  );
}