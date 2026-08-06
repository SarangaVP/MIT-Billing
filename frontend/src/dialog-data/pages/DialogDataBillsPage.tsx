import { useEffect, useState, useCallback } from "react";
import type { DialogDataBillPeriod, DialogDataBillLineItemOut } from "../types/dialogData";
import { listDialogDataBillPeriods, getDialogDataBillSummary, deleteDialogDataBillPeriod } from "../api/dialogData";
import DialogDataBillUploadPanel from "../components/DialogDataBillUploadPanel";
import DialogDataConfirmPanel from "../components/DialogDataConfirmPanel";

export default function DialogDataBillsPage() {
  const [periods, setPeriods] = useState<DialogDataBillPeriod[]>([]);
  const [loadingPeriods, setLoadingPeriods] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState<DialogDataBillPeriod | null>(null);
  const [summaryRows, setSummaryRows] = useState<DialogDataBillLineItemOut[]>([]);
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [showUpload, setShowUpload] = useState(false);
  const [search, setSearch] = useState("");
  const [deletingPeriod, setDeletingPeriod] = useState<DialogDataBillPeriod | null>(null);
  const [showBreakdown, setShowBreakdown] = useState(false);

  const loadPeriods = useCallback(async () => {
    setLoadingPeriods(true);
    try {
      setPeriods(await listDialogDataBillPeriods());
    } finally {
      setLoadingPeriods(false);
    }
  }, []);

  useEffect(() => {
    loadPeriods();
  }, [loadPeriods]);

  async function openPeriod(period: DialogDataBillPeriod) {
    setSelectedPeriod(period);
    setLoadingSummary(true);
    try {
      setSummaryRows(await getDialogDataBillSummary(period.id));
    } finally {
      setLoadingSummary(false);
    }
  }

  async function handleDeletePeriod() {
    if (!deletingPeriod) return;
    await deleteDialogDataBillPeriod(deletingPeriod.id);
    setDeletingPeriod(null);
    loadPeriods();
  }

  const filteredRows = summaryRows.filter((row) => {
    if (!search) return true;
    const pattern = search.toLowerCase();
    return (
      (row.connection_no ?? "").includes(search) ||
      (row.name ?? "").toLowerCase().includes(pattern) ||
      (row.emp_no ?? "").toLowerCase().includes(pattern)
    );
  });

  const money = (v: string | number | null) =>
    v == null ? "—" : `Rs. ${Number(v).toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
  const hasUsageData = summaryRows.some((r) => r.allocation_gb !== null);

  const teamCostRows = Object.entries(
    summaryRows.reduce<Record<string, number>>((acc, row) => {
      const team = row.team || "Unassigned";
      acc[team] = (acc[team] || 0) + Number(row.cost);
      return acc;
    }, {})
  )
    .map(([team, cost]) => ({ team, cost }))
    .sort((a, b) => a.team.localeCompare(b.team));
  const teamCostTotal = teamCostRows.reduce((sum, r) => sum + r.cost, 0);
  const sumOfLineItems = summaryRows.reduce((sum, r) => sum + Number(r.cost), 0);

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
              Net {money(selectedPeriod.net)} split across {selectedPeriod.users_count} connections at{" "}
              {money(selectedPeriod.per_user_cost)} each
              {!selectedPeriod.reconciled && selectedPeriod.reconciliation_discrepancy != null && (
                <> · off by {money(Math.abs(Number(selectedPeriod.reconciliation_discrepancy)))} (rounding)</>
              )}
            </p>
          </div>
          <button className="btn btn-ghost" onClick={() => setShowBreakdown((v) => !v)}>
            {showBreakdown ? "Hide" : "Show"} team cost & reconciliation
          </button>
        </div>

        {showBreakdown && (
          <div style={{ display: "flex", gap: 20, marginBottom: 20, flexWrap: "wrap" }}>
            <div className="table-wrap" style={{ flex: "1 1 320px" }}>
              <table>
                <thead>
                  <tr>
                    <th colSpan={2}>PDF vs Calculated</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Total Charges (PDF)</td>
                    <td className="mono">{money(selectedPeriod.total)}</td>
                  </tr>
                  <tr>
                    <td>VAT (PDF)</td>
                    <td className="mono">{money(selectedPeriod.vat)}</td>
                  </tr>
                  <tr>
                    <td>Net (Total − VAT)</td>
                    <td className="mono">{money(selectedPeriod.net)}</td>
                  </tr>
                  <tr>
                    <td>Sum of line items (calculated)</td>
                    <td className="mono">{money(sumOfLineItems)}</td>
                  </tr>
                  <tr>
                    <td>Difference</td>
                    <td
                      className="mono"
                      style={{ color: Math.abs(sumOfLineItems - Number(selectedPeriod.net || 0)) < 0.01 ? "var(--success)" : "var(--danger)" }}
                    >
                      {money(sumOfLineItems - Number(selectedPeriod.net || 0))}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div className="table-wrap" style={{ flex: "1 1 320px" }}>
              <table>
                <thead>
                  <tr>
                    <th>Team</th>
                    <th>Cost</th>
                  </tr>
                </thead>
                <tbody>
                  {teamCostRows.map((r) => (
                    <tr key={r.team}>
                      <td>{r.team}</td>
                      <td className="mono">{money(r.cost)}</td>
                    </tr>
                  ))}
                  <tr>
                    <td style={{ fontWeight: 600 }}>Grand Total</td>
                    <td className="mono" style={{ fontWeight: 600 }}>
                      {money(teamCostTotal)}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        )}

        <div className="toolbar">
          <input
            className="search-input"
            placeholder="Search by name, EMP No, or connection no…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>EMP No</th>
                <th>Name</th>
                <th>Team</th>
                <th>Connection No</th>
                {hasUsageData && (
                  <>
                    <th>Allocation</th>
                    <th>Usage</th>
                    <th>Remaining</th>
                    <th>Status</th>
                  </>
                )}
                <th>Cost</th>
              </tr>
            </thead>
            <tbody>
              {loadingSummary && (
                <tr>
                  <td colSpan={hasUsageData ? 9 : 5} className="empty-row">
                    Loading…
                  </td>
                </tr>
              )}
              {!loadingSummary && filteredRows.length === 0 && (
                <tr>
                  <td colSpan={hasUsageData ? 9 : 5} className="empty-row">
                    No rows match.
                  </td>
                </tr>
              )}
              {!loadingSummary &&
                filteredRows.map((row) => (
                  <tr key={row.id}>
                    <td className="mono">{row.emp_no}</td>
                    <td>{row.name}</td>
                    <td>{row.team || <span className="muted">—</span>}</td>
                    <td className="mono">{row.connection_no}</td>
                    {hasUsageData && (
                      <>
                        <td className="mono">{row.allocation_gb ?? "—"}</td>
                        <td className="mono">{row.usage_gb ?? "—"}</td>
                        <td className="mono">{row.remaining_gb ?? "—"}</td>
                        <td>{row.pay_go_status || <span className="muted">—</span>}</td>
                      </>
                    )}
                    <td className="mono">{money(row.cost)}</td>
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
          <h1>Dialog Data Bucket Bills</h1>
          <p className="page-subtitle">
            One master-account PDF per month, no per-connection breakdown — the app splits it across active
            connections.
          </p>
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
              <th>Bill Period</th>
              <th>Net</th>
              <th>Connections</th>
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
                  <td className="mono">
                    {p.period_start ?? "—"} — {p.period_end ?? "—"}
                  </td>
                  <td className="mono">{money(p.net)}</td>
                  <td className="mono">{p.users_count ?? "—"}</td>
                  <td>
                    {p.reconciled ? (
                      <span className="pill pill-active">Matched</span>
                    ) : (
                      <span className="pill pill-resigned">
                        Off by {money(Math.abs(Number(p.reconciliation_discrepancy ?? 0)))}
                      </span>
                    )}
                  </td>
                  <td className="actions-cell">
                    <button className="link-btn" onClick={() => openPeriod(p)}>
                      View summary
                    </button>
                    <button className="link-btn link-btn-danger" onClick={() => setDeletingPeriod(p)}>
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {showUpload && (
        <DialogDataBillUploadPanel
          onImported={() => {
            setShowUpload(false);
            loadPeriods();
          }}
          onCancel={() => setShowUpload(false)}
        />
      )}

      {deletingPeriod && (
        <DialogDataConfirmPanel
          title="Delete this bill?"
          message={`This removes "${deletingPeriod.label}" and all ${deletingPeriod.users_count ?? ""} line items permanently. This can't be undone.`}
          onConfirm={handleDeletePeriod}
          onCancel={() => setDeletingPeriod(null)}
        />
      )}
    </div>
  );
}