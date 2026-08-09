import { useEffect, useState, useCallback } from "react";
import type { SltGeneralBillPeriod, SltGeneralBillLineItem, SltGeneralAccount } from "../types/slt";
import {
  listSltGeneralBillPeriods, getSltGeneralBillLineItems, deleteSltGeneralBillPeriod,
  listSltGeneralAccounts, updateSltGeneralAccountLabel, deleteSltGeneralAccount,
} from "../api/slt";
import SltGeneralBillsUploadPanel from "../components/SltGeneralBillsUploadPanel";
import SltConfirmPanel from "../components/SltConfirmPanel";
import { exportTableToExcel } from "../../utils/exportTable";

export default function SltGeneralBillsPage() {
  const [periods, setPeriods] = useState<SltGeneralBillPeriod[]>([]);
  const [accounts, setAccounts] = useState<SltGeneralAccount[]>([]);
  const [loadingPeriods, setLoadingPeriods] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState<SltGeneralBillPeriod | null>(null);
  const [lineItems, setLineItems] = useState<SltGeneralBillLineItem[]>([]);
  const [loadingLineItems, setLoadingLineItems] = useState(false);
  const [showUpload, setShowUpload] = useState(false);
  const [deletingPeriod, setDeletingPeriod] = useState<SltGeneralBillPeriod | null>(null);
  const [editingAccountId, setEditingAccountId] = useState<string | null>(null);
  const [editingLabel, setEditingLabel] = useState("");
  const [deletingAccount, setDeletingAccount] = useState<SltGeneralAccount | null>(null);

  const loadAll = useCallback(async () => {
    setLoadingPeriods(true);
    try {
      const [periodsData, accountsData] = await Promise.all([listSltGeneralBillPeriods(), listSltGeneralAccounts()]);
      setPeriods(periodsData);
      setAccounts(accountsData);
    } finally {
      setLoadingPeriods(false);
    }
  }, []);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  async function openPeriod(period: SltGeneralBillPeriod) {
    setSelectedPeriod(period);
    setLoadingLineItems(true);
    try {
      setLineItems(await getSltGeneralBillLineItems(period.id));
    } finally {
      setLoadingLineItems(false);
    }
  }

  async function handleDeletePeriod() {
    if (!deletingPeriod) return;
    await deleteSltGeneralBillPeriod(deletingPeriod.id);
    setDeletingPeriod(null);
    loadAll();
  }

  async function handleSaveLabel(accountId: string) {
    await updateSltGeneralAccountLabel(accountId, editingLabel);
    setEditingAccountId(null);
    loadAll();
  }

  async function handleDeleteAccount() {
    if (!deletingAccount) return;
    await deleteSltGeneralAccount(deletingAccount.id);
    setDeletingAccount(null);
    loadAll();
  }

  const money = (v: string | number | null) =>
    v == null ? "—" : `Rs. ${Number(v).toLocaleString(undefined, { minimumFractionDigits: 2 })}`;

  const total = lineItems.reduce((sum, item) => sum + Number(item.amount), 0);
  const totalWithoutVat = lineItems
    .filter((item) => !item.description.toLowerCase().includes("vat"))
    .reduce((sum, item) => sum + Number(item.amount), 0);

  if (selectedPeriod) {
    return (
      <div className="page">
        <div className="page-header">
          <div>
            <button className="link-btn" onClick={() => setSelectedPeriod(null)} style={{ marginBottom: 8 }}>
              ← All bill periods
            </button>
            <h1>
              {selectedPeriod.account_label} — {selectedPeriod.label}
            </h1>
            <p className="page-subtitle">
              Account {selectedPeriod.account_no} · Total Charges for the Period {money(selectedPeriod.charges_for_period)}
            </p>
          </div>
          <button
            className="btn btn-ghost"
            onClick={() =>
              exportTableToExcel(
                ["Description", "Amount"],
                [
                  ...lineItems.map((item) => [item.description, Number(item.amount)]),
                  ["Total", Number(total.toFixed(2))],
                  ["Total without VAT", Number(totalWithoutVat.toFixed(2))],
                ],
                `SLT_${(selectedPeriod.account_label ?? selectedPeriod.account_no ?? "bill").replace(/\s+/g, "_")}_${selectedPeriod.label.replace(/\s+/g, "_")}.xlsx`,
                "Details"
              )
            }
          >
            Export to Excel
          </button>
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Description</th>
                <th>Amount</th>
              </tr>
            </thead>
            <tbody>
              {loadingLineItems && (
                <tr>
                  <td colSpan={2} className="empty-row">
                    Loading…
                  </td>
                </tr>
              )}
              {!loadingLineItems && lineItems.length === 0 && (
                <tr>
                  <td colSpan={2} className="empty-row">
                    No itemized charges recorded for this bill.
                  </td>
                </tr>
              )}
              {!loadingLineItems &&
                lineItems.map((item) => (
                  <tr key={item.id}>
                    <td>{item.description}</td>
                    <td className="mono">{money(item.amount)}</td>
                  </tr>
                ))}
              {!loadingLineItems && lineItems.length > 0 && (
                <>
                  <tr>
                    <td style={{ fontWeight: 600 }}>Total</td>
                    <td className="mono" style={{ fontWeight: 600 }}>
                      {money(total)}
                    </td>
                  </tr>
                  <tr>
                    <td style={{ fontWeight: 600 }}>Total without VAT</td>
                    <td className="mono" style={{ fontWeight: 600 }}>
                      {money(totalWithoutVat)}
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
          <h1>SLT General Bills</h1>
          <p className="page-subtitle">
            4 fixed accounts, no per-employee split — broadband, static IP, voice lines, PeoTV, business internet.
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowUpload(true)}>
          + Upload bills
        </button>
      </div>

      {accounts.length === 0 ? (
        <div className="field-group" style={{ marginBottom: 20 }}>
          <span className="field-label">Accounts</span>
          <p className="field-hint">
            No accounts yet — they're created automatically the first time you import a bill for them. If you
            expected to see accounts here, they may have been deleted; re-uploading a bill for that account
            number will bring it back.
          </p>
        </div>
      ) : (
        <div className="field-group" style={{ marginBottom: 20 }}>
          <span className="field-label">Accounts</span>
          {accounts.map((acc) => (
            <div key={acc.id} className="inline-row">
              <span className="mono">{acc.account_no}</span>
              {editingAccountId === acc.id ? (
                <>
                  <input value={editingLabel} onChange={(e) => setEditingLabel(e.target.value)} />
                  <button className="link-btn" onClick={() => handleSaveLabel(acc.id)}>
                    Save
                  </button>
                  <button className="link-btn" onClick={() => setEditingAccountId(null)}>
                    Cancel
                  </button>
                </>
              ) : (
                <>
                  <span>{acc.label}</span>
                  <button
                    className="link-btn"
                    onClick={() => {
                      setEditingAccountId(acc.id);
                      setEditingLabel(acc.label);
                    }}
                  >
                    Rename
                  </button>
                  <button className="link-btn link-btn-danger" onClick={() => setDeletingAccount(acc)}>
                    Delete
                  </button>
                </>
              )}
            </div>
          ))}
        </div>
      )}

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Account</th>
              <th>Month</th>
              <th>Bill Period</th>
              <th>Charges for Period</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {loadingPeriods && (
              <tr>
                <td colSpan={5} className="empty-row">
                  Loading…
                </td>
              </tr>
            )}
            {!loadingPeriods && periods.length === 0 && (
              <tr>
                <td colSpan={5} className="empty-row">
                  No bills imported yet.
                </td>
              </tr>
            )}
            {!loadingPeriods &&
              periods.map((p) => (
                <tr key={p.id}>
                  <td>
                    {p.account_label}
                    <div className="field-hint">{p.account_no}</div>
                  </td>
                  <td>{p.label}</td>
                  <td className="mono">
                    {p.period_start ?? "—"} — {p.period_end ?? "—"}
                  </td>
                  <td className="mono">{money(p.charges_for_period)}</td>
                  <td className="actions-cell">
                    <button className="link-btn" onClick={() => openPeriod(p)}>
                      View details
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
        <SltGeneralBillsUploadPanel
          onImported={() => {
            setShowUpload(false);
            loadAll();
          }}
          onCancel={() => setShowUpload(false)}
        />
      )}

      {deletingPeriod && (
        <SltConfirmPanel
          title="Delete this bill?"
          message={`This removes "${deletingPeriod.account_label} — ${deletingPeriod.label}" and its itemized charges permanently. This can't be undone.`}
          onConfirm={handleDeletePeriod}
          onCancel={() => setDeletingPeriod(null)}
        />
      )}

      {deletingAccount && (
        <SltConfirmPanel
          title="Delete this account?"
          message={`This hides "${deletingAccount.label}" from the accounts list. Any bills already imported for it stay exactly as they are — nothing historical is deleted.`}
          onConfirm={handleDeleteAccount}
          onCancel={() => setDeletingAccount(null)}
        />
      )}
    </div>
  );
}