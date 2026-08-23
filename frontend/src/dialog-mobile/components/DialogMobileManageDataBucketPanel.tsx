import { useState, type FormEvent } from "react";
import type { DialogMobileBillSummaryRow, DialogMobileLineItemChargeUpdateInput } from "../types/dialogMobile";

interface Props {
  rows: DialogMobileBillSummaryRow[];
  onSave: (lineItemId: string, payload: DialogMobileLineItemChargeUpdateInput) => Promise<void>;
  onCancel: () => void;
}

const emptyForm = {
  total_usage_charges: "",
  idd: "",
  roaming: "",
  charges_for_bill_period: "",
  vat: "",
  vas: "",
  add_to_bill_charges: "",
};

export default function DialogMobileManageDataBucketPanel({ rows, onSave, onCancel }: Props) {
  const [selectedId, setSelectedId] = useState("");
  const [search, setSearch] = useState("");
  const [showResults, setShowResults] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
    setForm({
      total_usage_charges: row.total_usage_charges,
      idd: row.idd,
      roaming: row.roaming,
      charges_for_bill_period: row.charges_for_bill_period,
      vat: row.vat,
      vas: row.vas,
      add_to_bill_charges: row.add_to_bill_charges,
    });
  }

  function handleSearchChange(value: string) {
    setSearch(value);
    setShowResults(true);
    if (selectedId) {
      setSelectedId("");
      setForm(emptyForm);
    }
  }

  function setField(field: keyof typeof form, value: string) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!selectedId) return;
    setError(null);
    setSaving(true);
    try {
      await onSave(selectedId, {
        total_usage_charges: Number(form.total_usage_charges),
        idd: Number(form.idd),
        roaming: Number(form.roaming),
        charges_for_bill_period: Number(form.charges_for_bill_period),
        vat: Number(form.vat),
        vas: Number(form.vas),
        add_to_bill_charges: Number(form.add_to_bill_charges),
      });
      setSelectedId("");
      setSearch("");
      setForm(emptyForm);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="panel-overlay" onClick={onCancel}>
      <form className="panel" onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
        <h2>Manage data bucket</h2>
        <p className="field-hint">
          Directly corrects a connection's raw charge figures for THIS bill period — Net Amount and Total
          recalculate automatically from these once saved. Use this for cases like a shared/General line whose
          real usage charge needs a manual fix.
        </p>

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
                      {row.name} <span className="mono muted">({row.emp_no})</span>
                    </span>
                    <div style={{ display: "flex", gap: 4, marginLeft: "auto" }}>
                      {row.project_label && <span className="pill pill-transferred">{row.project_label}</span>}
                      {row.is_general_line && <span className="pill pill-transferred">General Line</span>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </label>

        {selectedRow && (
          <>
            <div className="field-row">
              <label>
                Total Usage Charges
                <input type="number" step="0.01" required value={form.total_usage_charges} onChange={(e) => setField("total_usage_charges", e.target.value)} />
              </label>
              <label>
                IDD
                <input type="number" step="0.01" required value={form.idd} onChange={(e) => setField("idd", e.target.value)} />
              </label>
            </div>
            <div className="field-row">
              <label>
                Roaming
                <input type="number" step="0.01" required value={form.roaming} onChange={(e) => setField("roaming", e.target.value)} />
              </label>
              <label>
                VAS
                <input type="number" step="0.01" required value={form.vas} onChange={(e) => setField("vas", e.target.value)} />
              </label>
            </div>
            <div className="field-row">
              <label>
                Charges for Bill Period
                <input type="number" step="0.01" required value={form.charges_for_bill_period} onChange={(e) => setField("charges_for_bill_period", e.target.value)} />
              </label>
              <label>
                VAT
                <input type="number" step="0.01" required value={form.vat} onChange={(e) => setField("vat", e.target.value)} />
              </label>
            </div>
            <label>
              Add To Bill Charges
              <input type="number" step="0.01" required value={form.add_to_bill_charges} onChange={(e) => setField("add_to_bill_charges", e.target.value)} />
            </label>
            <p className="field-hint">
              Net Amount will be Rs.{" "}
              {(Number(form.charges_for_bill_period || 0) - Number(form.vat || 0)).toLocaleString(undefined, { minimumFractionDigits: 2 })}{" "}
              once saved (Charges for Bill Period − VAT).
            </p>
          </>
        )}

        {error && <p className="form-error">{error}</p>}

        <div className="panel-actions">
          <button type="button" className="btn btn-ghost" onClick={onCancel}>
            Close
          </button>
          <button type="submit" className="btn btn-primary" disabled={saving || !selectedRow}>
            {saving ? "Saving…" : "Save & recalculate"}
          </button>
        </div>
      </form>
    </div>
  );
}