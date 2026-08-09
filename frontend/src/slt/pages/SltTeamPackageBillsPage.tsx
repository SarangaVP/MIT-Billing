import { useEffect, useState, useCallback } from "react";
import type { SltTeamPackageBillPeriod, SltTeamPackageBillLineItem } from "../types/slt";
import { listSltTeamPackageBillPeriods, getSltTeamPackageBillSummary, deleteSltTeamPackageBillPeriod } from "../api/slt";
import SltTeamPackageUploadPanel from "../components/SltTeamPackageUploadPanel";
import SltConfirmPanel from "../components/SltConfirmPanel";
import { exportTableToExcel } from "../../utils/exportTable";

export default function SltTeamPackageBillsPage() {
  const [periods, setPeriods] = useState<SltTeamPackageBillPeriod[]>([]);
  const [loadingPeriods, setLoadingPeriods] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState<SltTeamPackageBillPeriod | null>(null);
  const [summaryRows, setSummaryRows] = useState<SltTeamPackageBillLineItem[]>([]);
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [showUpload, setShowUpload] = useState(false);
  const [search, setSearch] = useState("");
  const [deletingPeriod, setDeletingPeriod] = useState<SltTeamPackageBillPeriod | null>(null);

  const loadPeriods = useCallback(async () => {
    setLoadingPeriods(true);
    try {
      setPeriods(await listSltTeamPackageBillPeriods());
    } finally {
      setLoadingPeriods(false);
    }
  }, []);

  useEffect(() => {
    loadPeriods();
  }, [loadPeriods]);

  async function openPeriod(period: SltTeamPackageBillPeriod) {
    setSelectedPeriod(period);
    setLoadingSummary(true);
    try {
      setSummaryRows(await getSltTeamPackageBillSummary(period.id));
    } finally {
      setLoadingSummary(false);
    }
  }

  async function handleDeletePeriod() {
    if (!deletingPeriod) return;
    await deleteSltTeamPackageBillPeriod(deletingPeriod.id);
    setDeletingPeriod(null);
    loadPeriods();
  }

  const filteredRows = summaryRows.filter((row) => {
    if (!search) return true;
    const pattern = search.toLowerCase();
    return row.name.toLowerCase().includes(pattern) || (row.team ?? "").toLowerCase().includes(pattern);
  });

  const money = (v: string | number | null) =>
    v == null ? "—" : `Rs. ${Number(v).toLocaleString(undefined, { minimumFractionDigits: 2 })}`;

  if (selectedPeriod) {
    const packageSum = summaryRows.reduce((sum, r) => sum + Number(r.package_price), 0);
    const cess = Number(selectedPeriod.cess ?? 0);
    const sscl = Number(selectedPeriod.sscl ?? 0);
    const vat = Number(selectedPeriod.vat ?? 0);
    const totalWithoutVat = packageSum + cess + sscl;
    const total = totalWithoutVat + vat;

    return (
      <div className="page">
        <div className="page-header">
          <div>
            <button className="link-btn" onClick={() => setSelectedPeriod(null)} style={{ marginBottom: 8 }}>
              ← All bill periods
            </button>
            <h1>{selectedPeriod.label}</h1>
            <p className="page-subtitle">
              {selectedPeriod.users_count} employees, package sum {money(selectedPeriod.package_sum)} + Cess{" "}
              {money(selectedPeriod.cess)} + SSCL {money(selectedPeriod.sscl)} + VAT {money(selectedPeriod.vat)}
              {!selectedPeriod.reconciled && selectedPeriod.reconciliation_discrepancy != null && (
                <> · off by {money(Math.abs(Number(selectedPeriod.reconciliation_discrepancy)))} from the PDF's stated total</>
              )}
            </p>
          </div>
          <button
            className="btn btn-ghost"
            onClick={() =>
              exportTableToExcel(
                ["Name", "Team", "LOB Code", "Package", "Price"],
                [
                  ...summaryRows.map((row) => [row.name, row.team ?? "", row.lob_code ?? "", row.package_name, Number(row.package_price)]),
                  ["Package Sum", "", "", "", Number(packageSum.toFixed(2))],
                  ["Cess", "", "", "", Number(cess.toFixed(2))],
                  ["SSCL", "", "", "", Number(sscl.toFixed(2))],
                  ["VAT", "", "", "", Number(vat.toFixed(2))],
                  ["Total without VAT", "", "", "", Number(totalWithoutVat.toFixed(2))],
                  ["Total", "", "", "", Number(total.toFixed(2))],
                ],
                `SLT_TeamPackage_${selectedPeriod.label.replace(/\s+/g, "_")}.xlsx`,
                "Employees"
              )
            }
          >
            Export to Excel
          </button>
        </div>

        <div className="toolbar">
          <input
            className="search-input"
            placeholder="Search by name or team…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Team</th>
                <th>LOB Code</th>
                <th>Package</th>
                <th>Price</th>
              </tr>
            </thead>
            <tbody>
              {loadingSummary && (
                <tr>
                  <td colSpan={5} className="empty-row">
                    Loading…
                  </td>
                </tr>
              )}
              {!loadingSummary && filteredRows.length === 0 && (
                <tr>
                  <td colSpan={5} className="empty-row">
                    No rows match.
                  </td>
                </tr>
              )}
              {!loadingSummary &&
                filteredRows.map((row) => (
                  <tr key={row.id}>
                    <td>{row.name}</td>
                    <td>{row.team || <span className="muted">—</span>}</td>
                    <td className="mono">{row.lob_code || <span className="muted">—</span>}</td>
                    <td>{row.package_name}</td>
                    <td className="mono">{money(row.package_price)}</td>
                  </tr>
                ))}
              {!loadingSummary && filteredRows.length > 0 && (
                <>
                  <tr className="row-strong">
                    <td>Package Sum</td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td className="mono">
                      {money(packageSum)}
                    </td>
                  </tr>
                  <tr>
                    <td>Cess</td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td className="mono">{money(cess)}</td>
                  </tr>
                  <tr>
                    <td>SSCL</td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td className="mono">{money(sscl)}</td>
                  </tr>
                  <tr>
                    <td>VAT</td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td className="mono">{money(vat)}</td>
                  </tr>
                  <tr className="row-strong">
                    <td>Total without VAT</td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td className="mono">
                      {money(totalWithoutVat)}
                    </td>
                  </tr>
                  <tr className="row-strong">
                    <td>Total</td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td className="mono">
                      {money(total)}
                    </td>
                  </tr>
                </>
              )}
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
          <h1>SLT Team Package Bills</h1>
          <p className="page-subtitle">
            Account 004 767 150X — costs split by fixed package price per employee, from that month's Summary
            Excel.
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
              <th>Charges for Period</th>
              <th>Employees</th>
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
                  <td className="mono">{money(p.charges_for_period)}</td>
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
        <SltTeamPackageUploadPanel
          onImported={() => {
            setShowUpload(false);
            loadPeriods();
          }}
          onCancel={() => setShowUpload(false)}
        />
      )}

      {deletingPeriod && (
        <SltConfirmPanel
          title="Delete this bill?"
          message={`This removes "${deletingPeriod.label}" and all its line items permanently. This can't be undone.`}
          onConfirm={handleDeletePeriod}
          onCancel={() => setDeletingPeriod(null)}
        />
      )}
    </div>
  );
}