import { useState, type FormEvent } from "react";
import type { DialogMobileBillSummaryRow } from "../types/dialogMobile";

interface Props {
  periodLabel: string;
  rows: DialogMobileBillSummaryRow[];
  currentMobileNo: string | null;
  onSave: (mobileNo: string | null) => Promise<void>;
  onCancel: () => void;
}

export default function DialogMobileDataBucketPanel({ periodLabel, rows, currentMobileNo, onSave, onCancel }: Props) {
  const currentRow = rows.find((r) => r.mobile_no === currentMobileNo) || null;

  const [selectedId, setSelectedId] = useState("");
  const [search, setSearch] = useState("");
  const [showResults, setShowResults] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedRow = rows.find((r) => r.bill_line_item_id === selectedId) || null;

  const pattern = search.trim().toLowerCase();
  const filteredRows = pattern
    ? rows.filter(
        (r) =>
          (r.name ?? "").toLowerCase().includes(pattern) ||
          (r.emp_no ?? "").toLowerCase().includes(pattern) ||
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
    if (selectedId) setSelectedId("");
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!selectedRow) return;
    setError(null);
    setSaving(true);
    try {
      await onSave(selectedRow.mobile_no);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save");
    } finally {
      setSaving(false);
    }
  }

  async function handleClear() {
    setError(null);
    setSaving(true);
    try {
      await onSave(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not clear");
    } finally {
      setSaving(false);
    }
  }

  const money = (v: string | number) => `Rs. ${Number(v).toLocaleString(undefined, { minimumFractionDigits: 2 })}`;

  return (
    <div className="panel-overlay" onClick={onCancel}>
      <form className="panel" onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
        <h2>Select data bucket number for {periodLabel}</h2>
        <p className="field-hint">
          Pick the connection whose own Charges for Bill Period / VAT is the shared data bucket pool this
          month (e.g. the "Data bucket" General line). Bucket cost/VAT for every other eligible connection is
          then calculated automatically as an equal split of that pool — no manual rate entry needed. The
          chosen number is removed from the normal list and shown separately, and is automatically excluded
          from the bucket allocation itself. This only affects <strong>{periodLabel}</strong>.
        </p>

        {currentRow ? (
          <div className="field-group">
            <span className="field-label">Currently selected</span>
            <div className="inline-row">
              <span>
                {currentRow.mobile_no} {currentRow.name ? `— ${currentRow.name}` : ""}
              </span>
              <span className="mono muted">
                {money(currentRow.charges_for_bill_period)} charges · {money(currentRow.vat)} VAT
              </span>
              <button type="button" className="link-btn link-btn-danger" onClick={handleClear} disabled={saving}>
                Clear
              </button>
            </div>
          </div>
        ) : (
          <p className="field-hint">No data bucket number selected yet for this month — bucket cost/VAT falls back to the manual rate (or Rs. 0).</p>
        )}

        <label>
          Connection
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
                      {row.name} <span className="mono muted">({row.emp_no})</span> <span className="mono muted">{row.mobile_no}</span>
                    </span>
                    <div style={{ display: "flex", gap: 4, marginLeft: "auto" }}>
                      {row.is_data_bucket_line && <span className="pill pill-transferred">Current</span>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </label>

        {selectedRow && (
          <p className="field-hint">
            Pool this month: {money(selectedRow.charges_for_bill_period)} charges − {money(selectedRow.vat)} VAT ={" "}
            {money(Number(selectedRow.charges_for_bill_period) - Number(selectedRow.vat))} nett, split across every
            eligible connection.
          </p>
        )}

        {error && <p className="form-error">{error}</p>}

        <div className="panel-actions">
          <button type="button" className="btn btn-ghost" onClick={onCancel}>
            Close
          </button>
          <button type="submit" className="btn btn-primary" disabled={saving || !selectedRow}>
            {saving ? "Saving…" : "Save"}
          </button>
        </div>
      </form>
    </div>
  );
}