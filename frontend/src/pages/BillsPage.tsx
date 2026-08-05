import { useEffect, useState, useCallback } from "react";
import type { BillPeriod, BillSummaryRow } from "../types/bill";
import { listBillPeriods, getBillSummary, setApprovalOverride } from "../api/bills";
import BillUploadPanel from "../components/BillUploadPanel";

export default function BillsPage() {
  const [periods, setPeriods] = useState<BillPeriod[]>([]);
  const [loadingPeriods, setLoadingPeriods] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState<BillPeriod | null>(null);
  const [summaryRows, setSummaryRows] = useState<BillSummaryRow[]>([]);
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [showUpload, setShowUpload] = useState(false);
  const [search, setSearch] = useState("");

  const loadPeriods = useCallback(async () => {
    setLoadingPeriods(true);
    try {
      setPeriods(await listBillPeriods());
    } finally {
      setLoadingPeriods(false);
    }
  }, []);

  useEffect(() => {
    loadPeriods();
  }, [loadPeriods]);

  async function openPeriod(period: BillPeriod) {
    setSelectedPeriod(period);
    setLoadingSummary(true);
    try {
      setSummaryRows(await getBillSummary(period.id));
    } finally {
      setLoadingSummary(false);
    }
  }

  async function handleOverride(row: BillSummaryRow) {
    const value = prompt(
      'Override the approval status (e.g. "Manager approved"). Leave blank to clear the override.',
      row.is_overridden ? row.need_approval : ""
    );
    if (value === null) return;
    const updated = await setApprovalOverride(row.bill_line_item_id, { approval_override: value || null });
    setSummaryRows((rows) => rows.map((r) => (r.bill_line_item_id === updated.bill_line_item_id ? updated : r)));
  }

  const filteredRows = summaryRows.filter((row) => {
    if (!search) return true;
    const pattern = search.toLowerCase();
    return (
      row.mobile_no.includes(search) ||
      (row.name ?? "").toLowerCase().includes(pattern) ||
      (row.emp_no ?? "").toLowerCase().includes(pattern)
    );
  });

  const money = (v: number) => `Rs. ${Number(v).toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
  const hasBreakdown = summaryRows.some((r) => r.voice_rental !== null);

  if (selectedPeriod) {
    return (
      <div className="page">
        <div className="page-header">
          <div>
            <button className="link-btn" onClick={() => setSelectedPeriod(null)} style={{ marginBottom: 8 }}>
              ← All bill periods
            </button>
            <h1>{selectedPeriod.label}</h1>
            <p className="page-subtitle">
              Bill period {selectedPeriod.bill_period_start} to {selectedPeriod.bill_period_end} — imported from{" "}
              {selectedPeriod.source_format.toUpperCase()}
              {!selectedPeriod.reconciled && selectedPeriod.reconciliation_discrepancy != null && (
                <> · off by {money(Math.abs(selectedPeriod.reconciliation_discrepancy))} from the stated total</>
              )}
            </p>
          </div>
        </div>

        <div className="toolbar">
          <input
            className="search-input"
            placeholder="Search by name, EMP No, or mobile no…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Mobile No</th>
                <th>EMP No</th>
                <th>Name</th>
                {hasBreakdown && (
                  <>
                    <th>Voice</th>
                    <th>SMS</th>
                    <th>Data</th>
                  </>
                )}
                <th>Charges for Bill Period</th>
                <th>VAT</th>
                <th>Net Amount</th>
                <th>Bucket Cost</th>
                <th>Total</th>
                <th>Salary Deduction</th>
                <th>Need Approval</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {loadingSummary && (
                <tr>
                  <td colSpan={hasBreakdown ? 14 : 11} className="empty-row">
                    Loading…
                  </td>
                </tr>
              )}
              {!loadingSummary && filteredRows.length === 0 && (
                <tr>
                  <td colSpan={hasBreakdown ? 14 : 11} className="empty-row">
                    No rows match.
                  </td>
                </tr>
              )}
              {!loadingSummary &&
                filteredRows.map((row) => (
                  <tr key={row.bill_line_item_id}>
                    <td className="mono">{row.mobile_no}</td>
                    <td className="mono">{row.emp_no || <span className="muted">—</span>}</td>
                    <td>{row.name || <span className="muted">Unmatched number</span>}</td>
                    {hasBreakdown && (
                      <>
                        <td className="mono">
                          {row.voice_rental != null ? money((row.voice_rental ?? 0) + (row.voice_usage ?? 0)) : "—"}
                        </td>
                        <td className="mono">{row.sms != null ? money(row.sms) : "—"}</td>
                        <td className="mono">
                          {row.data_rental != null ? money((row.data_rental ?? 0) + (row.data_usage ?? 0)) : "—"}
                        </td>
                      </>
                    )}
                    <td className="mono">{money(row.charges_for_bill_period)}</td>
                    <td className="mono">{money(row.vat)}</td>
                    <td className="mono">{money(row.net_amount)}</td>
                    <td className="mono">{money(row.bucket_cost)}</td>
                    <td className="mono">{money(row.total)}</td>
                    <td className="mono">{row.salary_deduction > 0 ? money(row.salary_deduction) : "—"}</td>
                    <td>
                      <span className={`pill ${row.need_approval === "OK" ? "pill-active" : "pill-resigned"}`}>
                        {row.need_approval}
                      </span>
                      {row.is_overridden && <span className="field-hint"> (overridden)</span>}
                    </td>
                    <td>
                      <button className="link-btn" onClick={() => handleOverride(row)}>
                        Override
                      </button>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Bills</h1>
          <p className="page-subtitle">Monthly bill imports — parsed from PDF or .xls, reconciled automatically.</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowUpload(true)}>
          + Upload bill
        </button>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Month</th>
              <th>Source</th>
              <th>Bill Period</th>
              <th>Charges for Bill Period</th>
              <th>Reconciliation</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {loadingPeriods && (
              <tr>
                <td colSpan={6} className="empty-row">
                  Loading…
                </td>
              </tr>
            )}
            {!loadingPeriods && periods.length === 0 && (
              <tr>
                <td colSpan={6} className="empty-row">
                  No bills imported yet.
                </td>
              </tr>
            )}
            {!loadingPeriods &&
              periods.map((p) => (
                <tr key={p.id}>
                  <td>{p.label}</td>
                  <td>
                    <span className="pill pill-transferred">{p.source_format.toUpperCase()}</span>
                  </td>
                  <td className="mono">
                    {p.bill_period_start} — {p.bill_period_end}
                  </td>
                  <td className="mono">
                    {p.stated_total_charges_for_bill_period != null ? money(p.stated_total_charges_for_bill_period) : "—"}
                  </td>
                  <td>
                    {p.reconciled ? (
                      <span className="pill pill-active">Matched</span>
                    ) : (
                      <span className="pill pill-resigned" title={`Off by ${money(Math.abs(p.reconciliation_discrepancy ?? 0))}`}>
                        Off by {money(Math.abs(p.reconciliation_discrepancy ?? 0))}
                      </span>
                    )}
                  </td>
                  <td>
                    <button className="link-btn" onClick={() => openPeriod(p)}>
                      View summary
                    </button>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {showUpload && (
        <BillUploadPanel
          onImported={() => {
            setShowUpload(false);
            loadPeriods();
          }}
          onCancel={() => setShowUpload(false)}
        />
      )}
    </div>
  );
}