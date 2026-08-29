import { useEffect, useState, useCallback } from "react";
import type { DialogMobileBillPeriod, DialogMobileBillSummaryRow, DialogMobileLineItemChargeUpdateInput } from "../types/dialogMobile";
import { listDialogMobileBillPeriods, getDialogMobileBillSummary, setDialogMobileApprovalOverride, setDialogMobileSalaryDeductionOverride, setDialogMobileBucketExclusion, setDialogMobileBucketRateOverride, setDialogMobileDataBucketNumber, setDialogMobileLineItemCharges, deleteDialogMobileBillPeriod } from "../api/dialogMobile";
import DialogMobileBillUploadPanel from "../components/DialogMobileBillUploadPanel";
import DialogMobileBucketExclusionPanel from "../components/DialogMobileBucketExclusionPanel";
import DialogMobileBucketRatePanel from "../components/DialogMobileBucketRatePanel";
import DialogMobileDataBucketPanel from "../components/DialogMobileDataBucketPanel";
import DialogMobileManageDataBucketPanel from "../components/DialogMobileManageDataBucketPanel";
import DialogMobileConfirmPanel from "../components/DialogMobileConfirmPanel";
import { exportTableToExcel } from "../../utils/exportTable";
import { exportTeamCostToExcel } from "../../utils/exportTeamCost";

export default function DialogMobileBillsPage() {
  const [periods, setPeriods] = useState<DialogMobileBillPeriod[]>([]);
  const [loadingPeriods, setLoadingPeriods] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState<DialogMobileBillPeriod | null>(null);
  const [summaryRows, setSummaryRows] = useState<DialogMobileBillSummaryRow[]>([]);
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [showUpload, setShowUpload] = useState(false);
  const [search, setSearch] = useState("");
  const [approvalFilter, setApprovalFilter] = useState("");
  const [deletingPeriod, setDeletingPeriod] = useState<DialogMobileBillPeriod | null>(null);
  const [showBucketExclusionPanel, setShowBucketExclusionPanel] = useState(false);
  const [showBucketRatePanel, setShowBucketRatePanel] = useState(false);
  const [showDataBucketPanel, setShowDataBucketPanel] = useState(false);
  const [showManageDataBucketPanel, setShowManageDataBucketPanel] = useState(false);
  const [showBreakdown, setShowBreakdown] = useState(false);
  const [showProjectWorking, setShowProjectWorking] = useState(false);
  const [editingSalaryDeductionId, setEditingSalaryDeductionId] = useState<string | null>(null);
  const [salaryDeductionDraft, setSalaryDeductionDraft] = useState("");
  const [savingSalaryDeduction, setSavingSalaryDeduction] = useState(false);

  const loadPeriods = useCallback(async () => {
    setLoadingPeriods(true);
    try {
      setPeriods(await listDialogMobileBillPeriods());
    } finally {
      setLoadingPeriods(false);
    }
  }, []);

  useEffect(() => {
    loadPeriods();
  }, [loadPeriods]);

  async function openPeriod(period: DialogMobileBillPeriod) {
    setSelectedPeriod(period);
    setLoadingSummary(true);
    try {
      setSummaryRows(await getDialogMobileBillSummary(period.id));
    } finally {
      setLoadingSummary(false);
    }
  }

  async function handleApprovalChange(row: DialogMobileBillSummaryRow, value: string) {
    const updated = await setDialogMobileApprovalOverride(row.bill_line_item_id, { approval_override: value });
    setSummaryRows((rows) => rows.map((r) => (r.bill_line_item_id === updated.bill_line_item_id ? updated : r)));
  }

  function startEditSalaryDeduction(row: DialogMobileBillSummaryRow) {
    setEditingSalaryDeductionId(row.bill_line_item_id);
    setSalaryDeductionDraft(row.salary_deduction);
  }

  function cancelEditSalaryDeduction() {
    setEditingSalaryDeductionId(null);
    setSalaryDeductionDraft("");
  }

  async function saveSalaryDeductionOverride(lineItemId: string) {
    setSavingSalaryDeduction(true);
    try {
      const updated = await setDialogMobileSalaryDeductionOverride(lineItemId, {
        salary_deduction_override: salaryDeductionDraft === "" ? null : Number(salaryDeductionDraft),
      });
      setSummaryRows((rows) => rows.map((r) => (r.bill_line_item_id === updated.bill_line_item_id ? updated : r)));
      setEditingSalaryDeductionId(null);
      setSalaryDeductionDraft("");
    } finally {
      setSavingSalaryDeduction(false);
    }
  }

  async function clearSalaryDeductionOverride(lineItemId: string) {
    setSavingSalaryDeduction(true);
    try {
      const updated = await setDialogMobileSalaryDeductionOverride(lineItemId, { salary_deduction_override: null });
      setSummaryRows((rows) => rows.map((r) => (r.bill_line_item_id === updated.bill_line_item_id ? updated : r)));
      setEditingSalaryDeductionId(null);
      setSalaryDeductionDraft("");
    } finally {
      setSavingSalaryDeduction(false);
    }
  }

  async function handleSetBucketExclusion(lineItemId: string, isBucketExcluded: boolean) {
    await setDialogMobileBucketExclusion(lineItemId, { is_bucket_excluded: isBucketExcluded });
    // A single exclusion changes the eligible headcount for the whole
    // bill period, which shifts everyone else's bucket_cost/bucket_vat
    // too (whether split from an auto data bucket pool or not) — so the
    // full summary needs refetching, not just the one row that changed.
    if (selectedPeriod) {
      setSummaryRows(await getDialogMobileBillSummary(selectedPeriod.id));
    }
  }

  async function handleSetLineItemCharges(lineItemId: string, payload: DialogMobileLineItemChargeUpdateInput) {
    await setDialogMobileLineItemCharges(lineItemId, payload);
    // Editing charges can flip a connection's disconnected status (zero
    // usage/charges either way), which shifts the eligible headcount for
    // the whole bill period — same reasoning as bucket exclusion above.
    if (selectedPeriod) {
      setSummaryRows(await getDialogMobileBillSummary(selectedPeriod.id));
    }
  }

  function handleOpenBucketRatePanel() {
    setShowBucketRatePanel(true);
  }

  async function handleSaveBucketRate(cost: number | null, vat: number | null) {
    if (!selectedPeriod) return;
    const rows = await setDialogMobileBucketRateOverride(selectedPeriod.id, {
      bucket_cost_override: cost,
      bucket_vat_override: vat,
    });
    setSummaryRows(rows);
    setShowBucketRatePanel(false);
    // The override lives on the bill period itself, so refresh it too —
    // otherwise reopening this panel would show stale override values.
    const refreshedPeriods = await listDialogMobileBillPeriods();
    setPeriods(refreshedPeriods);
    const refreshed = refreshedPeriods.find((p) => p.id === selectedPeriod.id);
    if (refreshed) setSelectedPeriod(refreshed);
  }

  async function handleSaveDataBucketNumber(mobileNo: string | null) {
    if (!selectedPeriod) return;
    const rows = await setDialogMobileDataBucketNumber(selectedPeriod.id, { data_bucket_mobile_no: mobileNo });
    setSummaryRows(rows);
    setShowDataBucketPanel(false);
    // data_bucket_mobile_no lives on the bill period itself, so refresh it
    // too — otherwise reopening this panel would show a stale selection.
    const refreshedPeriods = await listDialogMobileBillPeriods();
    setPeriods(refreshedPeriods);
    const refreshed = refreshedPeriods.find((p) => p.id === selectedPeriod.id);
    if (refreshed) setSelectedPeriod(refreshed);
  }

  function approvalClass(value: string): string {
    if (value === "OK") return "approval-ok";
    if (value === "Need Approval") return "approval-attention";
    if (value === "Deducted from Salary") return "approval-salary-deducted";
    return "approval-manager"; // "Manager approved", or any other override text
  }

  async function handleDeletePeriod() {
    if (!deletingPeriod) return;
    await deleteDialogMobileBillPeriod(deletingPeriod.id);
    setDeletingPeriod(null);
    loadPeriods();
  }

  // The connection currently picked as the data bucket number — pulled out
  // of the normal table/sums entirely and rendered as its own row after
  // the Total row instead (see below).
  const dataBucketRow = summaryRows.find((r) => r.is_data_bucket_line) || null;
  const normalRows = summaryRows.filter((r) => !r.is_data_bucket_line);

  const filteredRows = normalRows.filter((row) => {
    if (approvalFilter && row.need_approval !== approvalFilter) return false;
    if (!search) return true;
    const pattern = search.toLowerCase();
    return (
      row.mobile_no.includes(search) ||
      (row.name ?? "").toLowerCase().includes(pattern) ||
      (row.emp_no ?? "").toLowerCase().includes(pattern)
    );
  });

  // Always the 4 standard values, plus any legacy free-text override
  // actually present this month — so all 4 real statuses are always
  // selectable, even in months where no one currently has, say,
  // "Deducted from Salary" set.
  const STANDARD_APPROVAL_STATUSES = ["OK", "Need Approval", "Manager approved", "Deducted from Salary"];
  const approvalOptions = [
    ...STANDARD_APPROVAL_STATUSES,
    ...new Set(normalRows.map((r) => r.need_approval).filter((v) => !STANDARD_APPROVAL_STATUSES.includes(v))),
  ];

  const money = (v: string | number) => `Rs. ${Number(v).toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
  const hasBreakdown = normalRows.some((r) => r.voice_rental !== null);

  // Groups every connection's Total by LOB, same pattern as Mobitel/Dialog
  // Data's own Team Cost breakdown — Dialog Mobile has no separate LOB
  // code field, so that column is always blank here. The data bucket
  // number is excluded (it's not a normal employee's cost).
  const teamCostRows = Object.entries(
    normalRows.reduce<Record<string, number>>((acc, row) => {
      const team = row.lob || "Unassigned";
      acc[team] = (acc[team] || 0) + Number(row.total);
      return acc;
    }, {})
  )
    .map(([team, cost]) => ({ team, code: null as string | null, cost }))
    .sort((a, b) => a.team.localeCompare(b.team));
  const teamCostTotal = teamCostRows.reduce((sum, r) => sum + r.cost, 0);

  // "Project Working" — a specific subset billed against project costs
  // rather than the department's own budget: everyone on Managed Services
  // or Cyber Security (regardless of cadre), plus anyone on ANY OTHER team
  // whose cadre is Fixed Term or Consultancy Contract (a project-funded
  // hire, wherever they happen to sit organizationally). The data bucket
  // number itself is never eligible here — it's excluded from normalRows
  // already.
  const PROJECT_WORKING_TEAMS = ["Managed Services", "Cyber Security"];
  const PROJECT_WORKING_CADRES = ["Fixed Term", "Consultancy Contract"];
  const projectWorkingRows = normalRows.filter(
    (row) =>
      (row.lob && PROJECT_WORKING_TEAMS.includes(row.lob)) ||
      (row.cadre && PROJECT_WORKING_CADRES.includes(row.cadre))
  );

  const sum = (key: keyof DialogMobileBillSummaryRow) => filteredRows.reduce((acc, r) => acc + Number(r[key] as string), 0);
  const totals = {
    total_usage_charges: sum("total_usage_charges"),
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
    late_payment_charges: sum("late_payment_charges"),
    salary_deduction: sum("salary_deduction"),
  };

  function handleExport() {
    if (!selectedPeriod) return;
    const headers = [
      "Mobile No", "EMP No", "Name", "Credit Limit", "Project", "Total Usage Charges",
      ...(hasBreakdown ? ["Voice Rental", "Voice Usage", "SMS", "Data Rental", "Data Usage"] : []),
      "IDD", "Roaming", "Charges for Bill Period", "VAT", "Net Amount", "Total - Credit Limit", "Bucket Cost", "Total",
      "VAS", "Add To Bill Charges", "Late Payment Charges", "Salary Deduction (VAS + Add To Bill Charges)", "Need Approval",
    ];
    const rows = filteredRows.map((row) => [
      row.mobile_no, row.emp_no ?? "", row.name ?? "Unmatched number",
      row.credit_limit != null ? Number(row.credit_limit) : "", row.project_label ?? "",
      Number(row.total_usage_charges),
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
      Number(row.net_amount), Number(row.total) - Number(row.credit_limit ?? 0),
      Number(row.bucket_cost), Number(row.total),
      Number(row.vas), Number(row.add_to_bill_charges), Number(row.late_payment_charges),
      Number(row.salary_deduction), row.need_approval,
    ]);
    const totalsRow = [
      "Total", "", "", "", "", Number(totals.total_usage_charges.toFixed(2)),
      ...(hasBreakdown
        ? [
            Number(totals.voice_rental.toFixed(2)), Number(totals.voice_usage.toFixed(2)), Number(totals.sms.toFixed(2)),
            Number(totals.data_rental.toFixed(2)), Number(totals.data_usage.toFixed(2)),
          ]
        : []),
      Number(totals.idd.toFixed(2)), Number(totals.roaming.toFixed(2)), Number(totals.charges_for_bill_period.toFixed(2)),
      Number(totals.vat.toFixed(2)), Number(totals.net_amount.toFixed(2)), "", Number(totals.bucket_cost.toFixed(2)),
      Number(totals.total.toFixed(2)), Number(totals.vas.toFixed(2)), Number(totals.add_to_bill_charges.toFixed(2)),
      Number(totals.late_payment_charges.toFixed(2)), Number(totals.salary_deduction.toFixed(2)), "",
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
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", justifyContent: "flex-end", minWidth: 0, rowGap: 10 }}>
            <button className="btn btn-ghost" onClick={() => setShowDataBucketPanel(true)}>
              {dataBucketRow ? "Change data bucket number" : "Select data bucket number"}
            </button>
            <button className="btn btn-ghost" onClick={handleOpenBucketRatePanel}>
              Set bucket rate manually
            </button>
            <button className="btn btn-ghost" onClick={() => setShowBucketExclusionPanel(true)}>
              Manage bucket exclusion
            </button>
            <button className="btn btn-ghost" onClick={() => setShowManageDataBucketPanel(true)}>
              Manage data bucket
            </button>
            <button className="btn btn-ghost" onClick={() => setShowBreakdown((v) => !v)}>
              {showBreakdown ? "Hide" : "Show"} team cost
            </button>
            <button className="btn btn-ghost" onClick={() => setShowProjectWorking((v) => !v)}>
              {showProjectWorking ? "Hide" : "Show"} project working
            </button>
            <button className="btn btn-ghost" onClick={handleExport}>
              Export to Excel
            </button>
          </div>
        </div>

        {summaryRows.length > 0 && (
          <div
            className="table-wrap"
            style={{ marginBottom: 20, padding: "10px 16px", display: "flex", gap: 24, flexWrap: "wrap", alignItems: "baseline" }}
          >
            <span>
              <strong>{summaryRows[0].eligible_employee_count}</strong> <span className="muted">eligible employees this month</span>
            </span>
            <span>
              <span className="muted">Bucket Nett</span> <strong className="mono">{money(summaryRows[0].standard_bucket_nett)}</strong>
            </span>
            <span>
              <span className="muted">Bucket VAT</span> <strong className="mono">{money(summaryRows[0].standard_bucket_vat)}</strong>
            </span>
            <span>
              <span className="muted">Bucket Cost</span> <strong className="mono">{money(summaryRows[0].standard_bucket_cost)}</strong>
            </span>
            <span className="field-hint" style={{ margin: 0 }}>
              {dataBucketRow
                ? "per eligible employee, split from the selected data bucket connection"
                : "per eligible employee, from the manual bucket rate"}
            </span>
          </div>
        )}

        {showBreakdown && (
          <div className="table-wrap" style={{ maxWidth: 460, marginBottom: 20 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 12px" }}>
              <strong style={{ fontSize: 13 }}>Team Cost</strong>
              <button
                type="button"
                className="link-btn"
                onClick={() =>
                  exportTeamCostToExcel(
                    teamCostRows,
                    teamCostTotal,
                    `DialogMobile_${selectedPeriod.label.replace(/\s+/g, "_")}_team_cost.xlsx`
                  )
                }
              >
                Export to Excel
              </button>
            </div>
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
                <tr className="row-strong">
                  <td>Grand Total</td>
                  <td className="mono">{money(teamCostTotal)}</td>
                </tr>
              </tbody>
            </table>
          </div>
        )}

        {showProjectWorking && (
          <div className="table-wrap" style={{ marginBottom: 20 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 12px" }}>
              <strong style={{ fontSize: 13 }}>Project Working</strong>
              <button
                type="button"
                className="link-btn"
                onClick={() =>
                  exportTableToExcel(
                    ["Mobile No", "Emp No", "Name", "Team", "Net Amount", "Salary deduction", "Late payment fee", "Cost"],
                    projectWorkingRows.map((row) => [
                      row.mobile_no,
                      row.emp_no ?? "",
                      row.name ?? "Unmatched number",
                      row.lob ?? "",
                      Number(row.net_amount),
                      Number(row.salary_deduction),
                      Number(row.late_payment_charges),
                      Number(row.net_amount) - Number(row.salary_deduction) - Number(row.late_payment_charges),
                    ]),
                    `DialogMobile_${selectedPeriod.label.replace(/\s+/g, "_")}_project_working.xlsx`,
                    "Project working"
                  )
                }
              >
                Export to Excel
              </button>
            </div>
            <table>
              <thead>
                <tr>
                  <th>Mobile No</th>
                  <th>Emp No</th>
                  <th>Name</th>
                  <th>Team</th>
                  <th>Net Amount</th>
                  <th>Salary deduction</th>
                  <th>Late payment fee</th>
                  <th>Cost</th>
                </tr>
              </thead>
              <tbody>
                {projectWorkingRows.length === 0 && (
                  <tr>
                    <td colSpan={8} className="empty-row">
                      No rows match — nobody on Managed Services/Cyber Security, or Fixed Term/Consultancy Contract elsewhere.
                    </td>
                  </tr>
                )}
                {projectWorkingRows.map((row) => {
                  const cost = Number(row.net_amount) - Number(row.salary_deduction) - Number(row.late_payment_charges);
                  return (
                    <tr key={row.bill_line_item_id}>
                      <td className="mono">{row.mobile_no}</td>
                      <td className="mono">{row.emp_no || <span className="muted">—</span>}</td>
                      <td>{row.name || <span className="muted">Unmatched number</span>}</td>
                      <td>{row.lob || <span className="muted">—</span>}</td>
                      <td className="mono">{money(row.net_amount)}</td>
                      <td className="mono">{Number(row.salary_deduction) > 0 ? money(row.salary_deduction) : "—"}</td>
                      <td className="mono">{Number(row.late_payment_charges) > 0 ? money(row.late_payment_charges) : "—"}</td>
                      <td className="mono">{money(cost)}</td>
                    </tr>
                  );
                })}
                {projectWorkingRows.length > 0 && (
                  <tr className="row-strong">
                    <td>Total</td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td className="mono">
                      {money(projectWorkingRows.reduce((acc, r) => acc + Number(r.net_amount), 0))}
                    </td>
                    <td className="mono">
                      {money(projectWorkingRows.reduce((acc, r) => acc + Number(r.salary_deduction), 0))}
                    </td>
                    <td className="mono">
                      {money(projectWorkingRows.reduce((acc, r) => acc + Number(r.late_payment_charges), 0))}
                    </td>
                    <td className="mono">
                      {money(
                        projectWorkingRows.reduce(
                          (acc, r) => acc + (Number(r.net_amount) - Number(r.salary_deduction) - Number(r.late_payment_charges)),
                          0
                        )
                      )}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        <div className="toolbar">
          <input
            className="search-input"
            placeholder="Search by name, EMP No, or mobile no…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <select value={approvalFilter} onChange={(e) => setApprovalFilter(e.target.value)}>
            <option value="">All approval statuses</option>
            {approvalOptions.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </select>
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Mobile No</th>
                <th>EMP No</th>
                <th>Name</th>
                <th>Credit Limit</th>
                <th>Project</th>
                <th>Total Usage Charges</th>
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
                <th>
                  <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
                    <span>Total − Credit Limit</span>
                    <span style={{ fontSize: 10, fontWeight: 400, textTransform: "none", letterSpacing: "normal", opacity: 0.7 }}>
                      (drives Need Approval)
                    </span>
                  </div>
                </th>
                <th>Bucket Cost</th>
                <th>Total</th>
                <th>VAS</th>
                <th>Add To Bill Charges</th>
                <th>Late Payment Charges</th>
                <th>
                  <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
                    <span>Salary Deduction</span>
                    <span style={{ fontSize: 10, fontWeight: 400, textTransform: "none", letterSpacing: "normal", opacity: 0.7 }}>
                      (VAS + Add To Bill Charges)
                    </span>
                  </div>
                </th>
                <th>Need Approval</th>
              </tr>
            </thead>
            <tbody>
              {loadingSummary && (
                <tr>
                  <td colSpan={hasBreakdown ? 24 : 19} className="empty-row">
                    Loading…
                  </td>
                </tr>
              )}
              {!loadingSummary && filteredRows.length === 0 && (
                <tr>
                  <td colSpan={hasBreakdown ? 24 : 19} className="empty-row">
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
                    <td className="mono">{row.credit_limit != null ? money(row.credit_limit) : <span className="muted">—</span>}</td>
                    <td>
                      {row.project_label ? (
                        <span className="pill pill-transferred">{row.project_label}</span>
                      ) : (
                        <span className="muted">—</span>
                      )}
                    </td>
                    <td className="mono">{money(row.total_usage_charges)}</td>
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
                    <td
                      className="mono"
                      style={{
                        color:
                          Number(row.total) - Number(row.credit_limit ?? 0) > 0 ? "var(--danger)" : "var(--success)",
                      }}
                    >
                      {money(Number(row.total) - Number(row.credit_limit ?? 0))}
                    </td>
                    <td className="mono">
                      {money(row.bucket_cost)}
                      {row.is_bucket_excluded && <span className="pill pill-transferred" style={{ marginLeft: 6 }}>Excluded</span>}
                    </td>
                    <td className="mono">{money(row.total)}</td>
                    <td className="mono">{Number(row.vas) > 0 ? money(row.vas) : "—"}</td>
                    <td className="mono">{Number(row.add_to_bill_charges) > 0 ? money(row.add_to_bill_charges) : "—"}</td>
                    <td className="mono">{Number(row.late_payment_charges) > 0 ? money(row.late_payment_charges) : "—"}</td>
                    <td className="mono">
                      {editingSalaryDeductionId === row.bill_line_item_id ? (
                        <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
                          <input
                            type="number"
                            step="0.01"
                            autoFocus
                            value={salaryDeductionDraft}
                            onChange={(e) => setSalaryDeductionDraft(e.target.value)}
                            style={{ width: 90 }}
                          />
                          <button
                            type="button"
                            className="link-btn"
                            disabled={savingSalaryDeduction}
                            onClick={() => saveSalaryDeductionOverride(row.bill_line_item_id)}
                          >
                            Save
                          </button>
                          <button type="button" className="link-btn" disabled={savingSalaryDeduction} onClick={cancelEditSalaryDeduction}>
                            ✕
                          </button>
                        </div>
                      ) : (
                        <span
                          style={{ cursor: "pointer" }}
                          title="Click to manually edit this amount"
                          onClick={() => startEditSalaryDeduction(row)}
                        >
                          {Number(row.salary_deduction) > 0 ? money(row.salary_deduction) : "—"}
                          {row.is_salary_deduction_overridden && (
                            <span className="pill pill-transferred" style={{ marginLeft: 6 }}>
                              Edited
                            </span>
                          )}
                        </span>
                      )}
                      {row.is_salary_deduction_overridden && editingSalaryDeductionId !== row.bill_line_item_id && (
                        <button
                          type="button"
                          className="link-btn link-btn-danger"
                          style={{ display: "block", fontSize: 11, marginTop: 2 }}
                          onClick={() => clearSalaryDeductionOverride(row.bill_line_item_id)}
                        >
                          Reset to computed
                        </button>
                      )}
                    </td>
                    <td>
                      <select
                        className={`mono approval-select ${approvalClass(row.need_approval)}`}
                        value={row.need_approval}
                        onChange={(e) => handleApprovalChange(row, e.target.value)}
                      >
                        <option value="OK" className="approval-option-ok">OK</option>
                        <option value="Need Approval" className="approval-option-attention">Need Approval</option>
                        <option value="Manager approved" className="approval-option-manager">Manager approved</option>
                        <option value="Deducted from Salary" className="approval-option-salary-deducted">Deducted from Salary</option>
                        {/* Preserve any other legacy free-text override so the select never shows blank */}
                        {!["OK", "Need Approval", "Manager approved", "Deducted from Salary"].includes(row.need_approval) && (
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
                  <td></td>
                  <td className="mono">{money(totals.total_usage_charges)}</td>
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
                  <td></td>
                  <td className="mono">{money(totals.bucket_cost)}</td>
                  <td className="mono">{money(totals.total)}</td>
                  <td className="mono">{money(totals.vas)}</td>
                  <td className="mono">{money(totals.add_to_bill_charges)}</td>
                  <td className="mono">{money(totals.late_payment_charges)}</td>
                  <td className="mono">{money(totals.salary_deduction)}</td>
                  <td></td>
                </tr>
              )}
              {!loadingSummary && dataBucketRow && (
                <tr className="row-strong" style={{ opacity: 0.9 }}>
                  <td className="mono">{dataBucketRow.mobile_no}</td>
                  <td className="mono">{dataBucketRow.emp_no || <span className="muted">—</span>}</td>
                  <td>
                    <span className="pill pill-transferred">Data Bucket</span> {dataBucketRow.name}
                  </td>
                  <td></td>
                  <td></td>
                  <td className="mono">{money(dataBucketRow.total_usage_charges)}</td>
                  {hasBreakdown && (
                    <>
                      <td className="mono">{dataBucketRow.voice_rental != null ? money(Number(dataBucketRow.voice_rental)) : "—"}</td>
                      <td className="mono">{dataBucketRow.voice_usage != null ? money(Number(dataBucketRow.voice_usage)) : "—"}</td>
                      <td className="mono">{dataBucketRow.sms != null ? money(Number(dataBucketRow.sms)) : "—"}</td>
                      <td className="mono">{dataBucketRow.data_rental != null ? money(Number(dataBucketRow.data_rental)) : "—"}</td>
                      <td className="mono">{dataBucketRow.data_usage != null ? money(Number(dataBucketRow.data_usage)) : "—"}</td>
                    </>
                  )}
                  <td className="mono">{money(dataBucketRow.idd)}</td>
                  <td className="mono">{money(dataBucketRow.roaming)}</td>
                  <td className="mono">{money(dataBucketRow.charges_for_bill_period)}</td>
                  <td className="mono">{money(dataBucketRow.vat)}</td>
                  <td></td>
                  <td></td>
                  <td className="mono">
                    {money(dataBucketRow.bucket_cost)}
                    <span className="pill pill-transferred" style={{ marginLeft: 6 }}>Excluded</span>
                  </td>
                  <td></td>
                  <td className="mono">{Number(dataBucketRow.vas) > 0 ? money(dataBucketRow.vas) : "—"}</td>
                  <td className="mono">{Number(dataBucketRow.add_to_bill_charges) > 0 ? money(dataBucketRow.add_to_bill_charges) : "—"}</td>
                  <td className="mono">{Number(dataBucketRow.late_payment_charges) > 0 ? money(dataBucketRow.late_payment_charges) : "—"}</td>
                  <td></td>
                  <td></td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {showBucketExclusionPanel && (
          <DialogMobileBucketExclusionPanel
            rows={normalRows}
            onSave={handleSetBucketExclusion}
            onCancel={() => setShowBucketExclusionPanel(false)}
          />
        )}

        {showManageDataBucketPanel && (
          <DialogMobileManageDataBucketPanel
            rows={normalRows}
            onSave={handleSetLineItemCharges}
            onCancel={() => setShowManageDataBucketPanel(false)}
          />
        )}

        {showBucketRatePanel && (
          <DialogMobileBucketRatePanel
            periodLabel={selectedPeriod.label}
            currentOverrideCost={selectedPeriod.bucket_cost_override}
            currentOverrideVat={selectedPeriod.bucket_vat_override}
            onSave={handleSaveBucketRate}
            onCancel={() => setShowBucketRatePanel(false)}
          />
        )}

        {showDataBucketPanel && (
          <DialogMobileDataBucketPanel
            periodLabel={selectedPeriod.label}
            rows={summaryRows}
            currentMobileNo={selectedPeriod.data_bucket_mobile_no}
            onSave={handleSaveDataBucketNumber}
            onCancel={() => setShowDataBucketPanel(false)}
          />
        )}
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
        <DialogMobileBillUploadPanel
          onImported={() => {
            setShowUpload(false);
            loadPeriods();
          }}
          onCancel={() => setShowUpload(false)}
        />
      )}

      {deletingPeriod && (
        <DialogMobileConfirmPanel
          title="Delete this bill?"
          message={`This removes "${deletingPeriod.label}" and all its line items permanently. This can't be undone.`}
          onConfirm={handleDeletePeriod}
          onCancel={() => setDeletingPeriod(null)}
        />
      )}
    </div>
  );
}