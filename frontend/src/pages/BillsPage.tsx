import { useEffect, useState, useCallback } from "react";
import type { BillPeriod, BillSummaryRow } from "../types/bill";
import { listBillPeriods, getBillSummary, setApprovalOverride, deleteBillPeriod } from "../api/bills";
import BillUploadPanel from "../components/BillUploadPanel";
import ConfirmPanel from "../components/ConfirmPanel";
import { exportTableToExcel } from "../utils/exportTable";

export default function BillsPage() {
  const [periods, setPeriods] = useState<BillPeriod[]>([]);
  const [loadingPeriods, setLoadingPeriods] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState<BillPeriod | null>(null);
  const [summaryRows, setSummaryRows] = useState<BillSummaryRow[]>([]);
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [showUpload, setShowUpload] = useState(false);
  const [search, setSearch] = useState("");
  const [deletingPeriod, setDeletingPeriod] = useState<BillPeriod | null>(null);

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

  async function handleApprovalChange(row: BillSummaryRow, value: string) {
    const updated = await setApprovalOverride(row.bill_line_item_id, { approval_override: value });
    setSummaryRows((rows) => rows.map((r) => (r.bill_line_item_id === updated.bill_line_item_id ? updated : r)));
  }

  function approvalClass(value: string): string {
    if (value === "OK") return "approval-ok";
    if (value === "Need Approval") return "approval-attention";
    return "approval-manager"; // "Manager approved", or any other override text
  }

  async function handleDeletePeriod() {
    if (!deletingPeriod) return;
    await deleteBillPeriod(deletingPeriod.id);
    setDeletingPeriod(null);
    loadPeriods();
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

  const money = (v: string | number) => `Rs. ${Number(v).toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
  const hasBreakdown = summaryRows.some((r) => r.voice_rental !== null);

  const sum = (key: keyof BillSummaryRow) => filteredRows.reduce((acc, r) => acc + Number(r[key] as string), 0);
  const totals = {
    voice_rental: sum("voice_rental"),
    voice_usage: sum("voice_usage"),
    sms: sum("sms"),
    data_rental: sum("data_rental"),
    data_usage: sum("data_usage"),
    idd: sum("idd"),
    roaming: sum("roaming"),
    charges_for_bill_period: sum("charges_for_bill_period"),
    vat: sum("vat"),
    net_amount: sum("net_amount"),
    bucket_cost: sum("bucket_cost"),
    total: sum("total"),
    vas: sum("vas"),
    add_to_bill_charges: sum("add_to_bill_charges"),
    salary_deduction: sum("salary_deduction"),
  };

  function handleExport() {
    if (!selectedPeriod) return;
    const headers = [
      "Mobile No", "EMP No", "Name", "Project",
      ...(hasBreakdown ? ["Voice Rental", "Voice Usage", "SMS", "Data Rental", "Data Usage"] : []),
      "IDD", "Roaming", "Charges for Bill Period", "VAT", "Net Amount", "Bucket Cost", "Total",
      "VAS", "Add To Bill Charges", "Salary Deduction", "Need Approval",
    ];
    const rows = filteredRows.map((row) => [
      row.mobile_no, row.emp_no ?? "", row.name ?? "Unmatched number", row.project_label ?? "",
      ...(hasBreakdown
        ? [
            row.voice_rental != null ? Number(row.voice_rental) : "",
            row.voice_usage != null ? Number(row.voice_usage) : "",
            row.sms != null ? Number(row.sms) : "",
            row.data_rental != null ? Number(row.data_rental) : "",
            row.data_usage != null ? Number(row.data_usage) : "",
          ]
        : []),
      Number(row.idd), Number(row.roaming), Number(row.charges_for_bill_period), Number(row.vat),
      Number(row.net_amount), Number(row.bucket_cost), Number(row.total),
      Number(row.vas), Number(row.add_to_bill_charges), Number(row.salary_deduction), row.need_approval,
    ]);
    const totalsRow = [
      "Total", "", "", "",
      ...(hasBreakdown
        ? [
            Number(totals.voice_rental.toFixed(2)), Number(totals.voice_usage.toFixed(2)), Number(totals.sms.toFixed(2)),
            Number(totals.data_rental.toFixed(2)), Number(totals.data_usage.toFixed(2)),
          ]
        : []),
      Number(totals.idd.toFixed(2)), Number(totals.roaming.toFixed(2)), Number(totals.charges_for_bill_period.toFixed(2)),
      Number(totals.vat.toFixed(2)), Number(totals.net_amount.toFixed(2)), Number(totals.bucket_cost.toFixed(2)),
      Number(totals.total.toFixed(2)), Number(totals.vas.toFixed(2)), Number(totals.add_to_bill_charges.toFixed(2)),
      Number(totals.salary_deduction.toFixed(2)), "",
    ];
    exportTableToExcel(
      headers,
      [...rows, totalsRow],
      `DialogMobile_${selectedPeriod.label.replace(/\s+/g, "_")}.xlsx`,
      "Summary"
    );
  }

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
                <> · off by {money(Math.abs(Number(selectedPeriod.reconciliation_discrepancy)))} from the stated total</>
              )}
            </p>
          </div>
          <button className="btn btn-ghost" onClick={handleExport}>
            Export to Excel
          </button>
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
                <th>Project</th>
                {hasBreakdown && (
                  <>
                    <th>Voice Rental</th>
                    <th>Voice Usage</th>
                    <th>SMS</th>
                    <th>Data Rental</th>
                    <th>Data Usage</th>
                  </>
                )}
                <th>IDD</th>
                <th>Roaming</th>
                <th>Charges for Bill Period</th>
                <th>VAT</th>
                <th>Net Amount</th>
                <th>Bucket Cost</th>
                <th>Total</th>
                <th>VAS</th>
                <th>Add To Bill Charges</th>
                <th>Salary Deduction</th>
                <th>Need Approval</th>
              </tr>
            </thead>
            <tbody>
              {loadingSummary && (
                <tr>
                  <td colSpan={hasBreakdown ? 20 : 15} className="empty-row">
                    Loading…
                  </td>
                </tr>
              )}
              {!loadingSummary && filteredRows.length === 0 && (
                <tr>
                  <td colSpan={hasBreakdown ? 20 : 15} className="empty-row">
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
                    <td>
                      {row.project_label ? (
                        <span className="pill pill-transferred">{row.project_label}</span>
                      ) : (
                        <span className="muted">—</span>
                      )}
                    </td>
                    {hasBreakdown && (
                      <>
                        <td className="mono">{row.voice_rental != null ? money(Number(row.voice_rental)) : "—"}</td>
                        <td className="mono">{row.voice_usage != null ? money(Number(row.voice_usage)) : "—"}</td>
                        <td className="mono">{row.sms != null ? money(Number(row.sms)) : "—"}</td>
                        <td className="mono">{row.data_rental != null ? money(Number(row.data_rental)) : "—"}</td>
                        <td className="mono">{row.data_usage != null ? money(Number(row.data_usage)) : "—"}</td>
                      </>
                    )}
                    <td className="mono">{money(row.idd)}</td>
                    <td className="mono">{money(row.roaming)}</td>
                    <td className="mono">{money(row.charges_for_bill_period)}</td>
                    <td className="mono">{money(row.vat)}</td>
                    <td className="mono">{money(row.net_amount)}</td>
                    <td className="mono">{money(row.bucket_cost)}</td>
                    <td className="mono">{money(row.total)}</td>
                    <td className="mono">{Number(row.vas) > 0 ? money(row.vas) : "—"}</td>
                    <td className="mono">{Number(row.add_to_bill_charges) > 0 ? money(row.add_to_bill_charges) : "—"}</td>
                    <td className="mono">{Number(row.salary_deduction) > 0 ? money(row.salary_deduction) : "—"}</td>
                    <td>
                      <select
                        className={`mono approval-select ${approvalClass(row.need_approval)}`}
                        value={row.need_approval}
                        onChange={(e) => handleApprovalChange(row, e.target.value)}
                      >
                        <option value="OK" className="approval-option-ok">OK</option>
                        <option value="Need Approval" className="approval-option-attention">Need Approval</option>
                        <option value="Manager approved" className="approval-option-manager">Manager approved</option>
                        {/* Preserve any other legacy free-text override so the select never shows blank */}
                        {!["OK", "Need Approval", "Manager approved"].includes(row.need_approval) && (
                          <option value={row.need_approval}>{row.need_approval}</option>
                        )}
                      </select>
                    </td>
                  </tr>
                ))}
              {!loadingSummary && filteredRows.length > 0 && (
                <tr className="row-strong">
                  <td>Total</td>
                  <td></td>
                  <td></td>
                  <td></td>
                  {hasBreakdown && (
                    <>
                      <td className="mono">{money(totals.voice_rental)}</td>
                      <td className="mono">{money(totals.voice_usage)}</td>
                      <td className="mono">{money(totals.sms)}</td>
                      <td className="mono">{money(totals.data_rental)}</td>
                      <td className="mono">{money(totals.data_usage)}</td>
                    </>
                  )}
                  <td className="mono">{money(totals.idd)}</td>
                  <td className="mono">{money(totals.roaming)}</td>
                  <td className="mono">{money(totals.charges_for_bill_period)}</td>
                  <td className="mono">{money(totals.vat)}</td>
                  <td className="mono">{money(totals.net_amount)}</td>
                  <td className="mono">{money(totals.bucket_cost)}</td>
                  <td className="mono">{money(totals.total)}</td>
                  <td className="mono">{money(totals.vas)}</td>
                  <td className="mono">{money(totals.add_to_bill_charges)}</td>
                  <td className="mono">{money(totals.salary_deduction)}</td>
                  <td></td>
                </tr>
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
                      <span className="pill pill-resigned" title={`Off by ${money(Math.abs(Number(p.reconciliation_discrepancy ?? 0)))}`}>
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
        <BillUploadPanel
          onImported={() => {
            setShowUpload(false);
            loadPeriods();
          }}
          onCancel={() => setShowUpload(false)}
        />
      )}

      {deletingPeriod && (
        <ConfirmPanel
          title="Delete this bill?"
          message={`This removes "${deletingPeriod.label}" and all its line items permanently. This can't be undone.`}
          onConfirm={handleDeletePeriod}
          onCancel={() => setDeletingPeriod(null)}
        />
      )}
    </div>
  );
}