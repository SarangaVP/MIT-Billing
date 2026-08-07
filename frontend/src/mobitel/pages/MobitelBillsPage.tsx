import { useEffect, useState, useCallback } from "react";
import type { MobitelBillPeriod, MobitelBillLineItemOut } from "../types/mobitel";
import { listMobitelBillPeriods, getMobitelBillSummary, setMobitelStaticIpCost, deleteMobitelBillPeriod } from "../api/mobitel";
import MobitelBillUploadPanel from "../components/MobitelBillUploadPanel";
import MobitelStaticIpCostPanel from "../components/MobitelStaticIpCostPanel";
import MobitelConfirmPanel from "../components/MobitelConfirmPanel";

export default function MobitelBillsPage() {
  const [periods, setPeriods] = useState<MobitelBillPeriod[]>([]);
  const [loadingPeriods, setLoadingPeriods] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState<MobitelBillPeriod | null>(null);
  const [summaryRows, setSummaryRows] = useState<MobitelBillLineItemOut[]>([]);
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [showUpload, setShowUpload] = useState(false);
  const [search, setSearch] = useState("");
  const [editingStaticIp, setEditingStaticIp] = useState<MobitelBillLineItemOut | null>(null);
  const [deletingPeriod, setDeletingPeriod] = useState<MobitelBillPeriod | null>(null);
  const [showBreakdown, setShowBreakdown] = useState(false);

  const loadPeriods = useCallback(async () => {
    setLoadingPeriods(true);
    try {
      setPeriods(await listMobitelBillPeriods());
    } finally {
      setLoadingPeriods(false);
    }
  }, []);

  useEffect(() => {
    loadPeriods();
  }, [loadPeriods]);

  async function openPeriod(period: MobitelBillPeriod) {
    setSelectedPeriod(period);
    setLoadingSummary(true);
    try {
      setSummaryRows(await getMobitelBillSummary(period.id));
    } finally {
      setLoadingSummary(false);
    }
  }

  async function handleSetStaticIpCost(cost: string) {
    if (!editingStaticIp) return;
    const rows = await setMobitelStaticIpCost(editingStaticIp.id, cost);
    setSummaryRows(rows);
    setEditingStaticIp(null);
    // Keep BOTH the detail view (selectedPeriod) and the main list (periods)
    // in sync with the recalculation — previously only selectedPeriod was
    // updated, so going "back" to the list showed a stale reconciliation
    // value until a manual page refresh.
    const refreshedPeriods = await listMobitelBillPeriods();
    setPeriods(refreshedPeriods);
    if (selectedPeriod) {
      const refreshed = refreshedPeriods.find((p) => p.id === selectedPeriod.id);
      if (refreshed) setSelectedPeriod(refreshed);
    }
  }

  async function handleDeletePeriod() {
    if (!deletingPeriod) return;
    await deleteMobitelBillPeriod(deletingPeriod.id);
    setDeletingPeriod(null);
    loadPeriods();
  }

  const filteredRows = summaryRows.filter((row) => {
    if (!search) return true;
    const pattern = search.toLowerCase();
    return (
      (row.mobile_no ?? "").includes(search) ||
      (row.name ?? "").toLowerCase().includes(pattern) ||
      (row.emp_no ?? "").toLowerCase().includes(pattern)
    );
  });

  const money = (v: string | number | null) =>
    v == null ? "—" : `Rs. ${Number(v).toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
  const mb = (v: string | number | null) => (v == null ? "—" : `${Number(v).toLocaleString()} Mb`);
  const hasUsageData = summaryRows.some((r) => r.imsi_number !== null);

  // "Team cost" breakdown — groups every employee's Total by LOB, same as
  // the source Excel's own "Team cost" sheet (verified to reproduce it
  // exactly, aside from one known Rs. 0.34 manual-correction anomaly that
  // existed in the original sheet itself). Also carries the numeric LOB
  // code alongside the team name, when present (only in newer file exports).
  const teamCostRows = Object.entries(
    summaryRows.reduce<Record<string, { cost: number; code: string | null }>>((acc, row) => {
      const team = row.lob || "Unassigned";
      if (!acc[team]) acc[team] = { cost: 0, code: row.lob_code };
      acc[team].cost += Number(row.total);
      return acc;
    }, {})
  )
    .map(([team, { cost, code }]) => ({ team, cost, code }))
    .sort((a, b) => a.team.localeCompare(b.team));
  const teamCostTotal = teamCostRows.reduce((sum, r) => sum + r.cost, 0);

  // "PDF vs Calculated" reconciliation — the PDF's own stated figures next
  // to what we actually computed and summed, so a mismatch is visible at a
  // glance rather than only available as a single "off by Rs. X" pill.
  const sumOfLineItems = summaryRows.reduce((sum, r) => sum + Number(r.total), 0);

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
              Net {money(selectedPeriod.net)} split across {selectedPeriod.users_count} employees at{" "}
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
                    <td>Bucket Total (PDF)</td>
                    <td className="mono">{money(selectedPeriod.bucket_total)}</td>
                  </tr>
                  <tr>
                    <td>VAT (PDF)</td>
                    <td className="mono">{money(selectedPeriod.vat)}</td>
                  </tr>
                  <tr>
                    <td>Net (Bucket − VAT)</td>
                    <td className="mono">{money(selectedPeriod.net)}</td>
                  </tr>
                  <tr>
                    <td>Sum of line items (calculated)</td>
                    <td className="mono">{money(sumOfLineItems)}</td>
                  </tr>
                  <tr>
                    <td>Difference</td>
                    <td className="mono" style={{ color: Math.abs(sumOfLineItems - Number(selectedPeriod.net || 0)) < 0.01 ? "var(--success)" : "var(--danger)" }}>
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
                    <th>LOB Code</th>
                    <th>Cost</th>
                  </tr>
                </thead>
                <tbody>
                  {teamCostRows.map((r) => (
                    <tr key={r.team}>
                      <td>{r.team}</td>
                      <td className="mono">{r.code || <span className="muted">—</span>}</td>
                      <td className="mono">{money(r.cost)}</td>
                    </tr>
                  ))}
                  <tr>
                    <td style={{ fontWeight: 600 }}>Grand Total</td>
                    <td></td>
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
            placeholder="Search by name, EMP No, or mobile no…"
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
                <th>Mobile No</th>
                <th>LOB</th>
                <th>LOB Code</th>
                {hasUsageData && (
                  <>
                    <th>IMSI</th>
                    <th>Data Allocated</th>
                    <th>Data Available</th>
                    <th>Data Utilized</th>
                    <th>Daily Limit</th>
                    <th>Member Status</th>
                  </>
                )}
                <th>Data Cost</th>
                <th>Static IP Cost</th>
                <th>Total</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {loadingSummary && (
                <tr>
                  <td colSpan={hasUsageData ? 15 : 9} className="empty-row">
                    Loading…
                  </td>
                </tr>
              )}
              {!loadingSummary && filteredRows.length === 0 && (
                <tr>
                  <td colSpan={hasUsageData ? 15 : 9} className="empty-row">
                    No rows match.
                  </td>
                </tr>
              )}
              {!loadingSummary &&
                filteredRows.map((row) => (
                  <tr key={row.id}>
                    <td className="mono">{row.emp_no}</td>
                    <td>{row.name}</td>
                    <td className="mono">{row.mobile_no}</td>
                    <td>{row.lob || <span className="muted">—</span>}</td>
                    <td className="mono">{row.lob_code || <span className="muted">—</span>}</td>
                    {hasUsageData && (
                      <>
                        <td className="mono">{row.imsi_number || "—"}</td>
                        <td className="mono">{mb(row.data_volume_mb)}</td>
                        <td className="mono">{mb(row.available_data_volume_mb)}</td>
                        <td className="mono">{mb(row.utilized_data_volume_mb)}</td>
                        <td className="mono">{mb(row.daily_limit_mb)}</td>
                        <td>{row.member_status || <span className="muted">—</span>}</td>
                      </>
                    )}
                    <td className="mono">{money(row.data_cost)}</td>
                    <td className="mono">{Number(row.static_ip_cost) > 0 ? money(row.static_ip_cost) : "—"}</td>
                    <td className="mono">{money(row.total)}</td>
                    <td>
                      <button className="link-btn" onClick={() => setEditingStaticIp(row)}>
                        Set static IP
                      </button>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>

        {editingStaticIp && (
          <MobitelStaticIpCostPanel
            row={editingStaticIp}
            onSave={handleSetStaticIpCost}
            onCancel={() => setEditingStaticIp(null)}
          />
        )}
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Mobitel Bills</h1>
          <p className="page-subtitle">
            Mobitel data bucket bill has no per-employee breakdown — the app splits it across active employees.
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
              <th>Users</th>
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
        <MobitelBillUploadPanel
          onImported={() => {
            setShowUpload(false);
            loadPeriods();
          }}
          onCancel={() => setShowUpload(false)}
        />
      )}

      {deletingPeriod && (
        <MobitelConfirmPanel
          title="Delete this bill?"
          message={`This removes "${deletingPeriod.label}" and all ${deletingPeriod.users_count ?? ""} line items permanently. This can't be undone.`}
          onConfirm={handleDeletePeriod}
          onCancel={() => setDeletingPeriod(null)}
        />
      )}
    </div>
  );
}