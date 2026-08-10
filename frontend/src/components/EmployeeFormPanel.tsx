import { useState, type FormEvent } from "react";
import type { Employee, EmployeeCreateInput, EmployeeUpdateInput } from "../types/employee";
import { addMobileNumber, removeMobileNumber, updateMobileNumberProjectLabel } from "../api/employees";

interface Props {
  employee: Employee | null; // null = creating a new employee
  onSave: (payload: EmployeeCreateInput | EmployeeUpdateInput) => Promise<void>;
  onNumbersChanged: () => void; // called after an inline add/remove, so the parent refetches
  onCancel: () => void;
}

interface FormState {
  emp_no: string;
  name: string;
  mobile_no: string; // only used when creating
  lob: string;
  cadre: string;
  level: string;
  credit_limit: string;
  email: string;
  resignation: string;
}

const EMPTY: FormState = {
  emp_no: "",
  name: "",
  mobile_no: "",
  lob: "",
  cadre: "",
  level: "",
  credit_limit: "",
  email: "",
  resignation: "No",
};

export default function EmployeeFormPanel({ employee, onSave, onNumbersChanged, onCancel }: Props) {
  const isEdit = employee !== null;
  const [form, setForm] = useState<FormState>(
    employee
      ? {
          emp_no: employee.emp_no,
          name: employee.name,
          mobile_no: "",
          lob: employee.lob ?? "",
          cadre: employee.cadre ?? "",
          level: employee.level ?? "",
          credit_limit: employee.credit_limit != null ? String(employee.credit_limit) : "",
          email: employee.email ?? "",
          resignation: employee.resignation ?? "",
        }
      : EMPTY
  );
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const [newNumber, setNewNumber] = useState("");
  const [numberBusy, setNumberBusy] = useState(false);
  const [numberError, setNumberError] = useState<string | null>(null);
  const [editingLabelFor, setEditingLabelFor] = useState<string | null>(null);
  const [labelInput, setLabelInput] = useState("");

  const activeNumbers = employee ? employee.mobile_numbers.filter((n) => n.status === "active") : [];

  function update<K extends keyof FormState>(field: K, value: FormState[K]) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      const shared = {
        emp_no: form.emp_no,
        name: form.name,
        lob: form.lob || null,
        cadre: form.cadre || null,
        level: form.level || null,
        credit_limit: form.credit_limit === "" ? null : Number(form.credit_limit),
        email: form.email || null,
        resignation: form.resignation || null,
      };

      if (isEdit) {
        await onSave(shared as EmployeeUpdateInput);
      } else {
        await onSave({ ...shared, mobile_no: form.mobile_no || null } as EmployeeCreateInput);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setSaving(false);
    }
  }

  async function handleAddNumber() {
    if (!employee || !newNumber.trim()) return;
    setNumberError(null);
    setNumberBusy(true);
    try {
      await addMobileNumber(employee.id, { mobile_no: newNumber.trim() });
      setNewNumber("");
      onNumbersChanged();
    } catch (err) {
      setNumberError(err instanceof Error ? err.message : "Could not add number");
    } finally {
      setNumberBusy(false);
    }
  }

  async function handleRemoveNumber(numberId: string) {
    if (!employee) return;
    if (!confirm("Mark this number as inactive? It stays in billing history.")) return;
    setNumberError(null);
    setNumberBusy(true);
    try {
      await removeMobileNumber(employee.id, numberId);
      onNumbersChanged();
    } catch (err) {
      setNumberError(err instanceof Error ? err.message : "Could not remove number");
    } finally {
      setNumberBusy(false);
    }
  }

  async function handleSaveLabel(numberId: string) {
    setNumberError(null);
    try {
      await updateMobileNumberProjectLabel(numberId, labelInput.trim() || null);
      setEditingLabelFor(null);
      onNumbersChanged();
    } catch (err) {
      setNumberError(err instanceof Error ? err.message : "Could not save project label");
    }
  }

  return (
    <div className="panel-overlay" onClick={onCancel}>
      <form className="panel" onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
        <h2>{isEdit ? "Edit employee" : "Add employee"}</h2>

        <label>
          EMP No
          <input
            required
            disabled={isEdit}
            value={form.emp_no}
            onChange={(e) => update("emp_no", e.target.value)}
            placeholder="77959 or PC0007"
          />
        </label>

        <label>
          Name
          <input required value={form.name} onChange={(e) => update("name", e.target.value)} />
        </label>

        <div className="field-row">
          <label>
            LOB
            <input value={form.lob} onChange={(e) => update("lob", e.target.value)} placeholder="e.g. Cyber Security" />
          </label>
          <label>
            Cadre
            <input value={form.cadre} onChange={(e) => update("cadre", e.target.value)} />
          </label>
        </div>

        <div className="field-row">
          <label>
            Level
            <input value={form.level} onChange={(e) => update("level", e.target.value)} placeholder="e.g. L1" />
          </label>
          <label>
            Credit Limit
            <input
              type="number"
              step="0.01"
              value={form.credit_limit}
              onChange={(e) => update("credit_limit", e.target.value)}
            />
          </label>
        </div>

        <label>
          Email
          <input value={form.email} onChange={(e) => update("email", e.target.value)} />
        </label>

        <label>
          Resignation
          <input
            value={form.resignation}
            onChange={(e) => update("resignation", e.target.value)}
            placeholder='"No" or a date, e.g. 23.01.26'
          />
        </label>

        {!isEdit && (
          <label>
            Mobile No <span className="field-hint">(optional — some employees have none)</span>
            <input
              value={form.mobile_no}
              onChange={(e) => update("mobile_no", e.target.value)}
              placeholder="740052313"
            />
          </label>
        )}

        {isEdit && (
          <div>
            <p className="field-hint" style={{ marginBottom: 6 }}>
              Mobile numbers
            </p>
            {activeNumbers.length === 0 && <p className="field-hint">No active numbers.</p>}
            <ul className="number-list">
              {activeNumbers.map((n) => (
                <li key={n.id} className="number-list-item">
                  <span className="mono">{n.mobile_no}</span>
                  {n.is_primary && <span className="pill pill-active">Primary</span>}
                  {n.project_label && <span className="pill pill-transferred">{n.project_label}</span>}
                  {editingLabelFor === n.id ? (
                    <>
                      <input
                        className="mono"
                        style={{ maxWidth: 140 }}
                        value={labelInput}
                        onChange={(e) => setLabelInput(e.target.value)}
                        placeholder="Project label"
                      />
                      <button type="button" className="link-btn" onClick={() => handleSaveLabel(n.id)}>
                        Save
                      </button>
                      <button type="button" className="link-btn" onClick={() => setEditingLabelFor(null)}>
                        Cancel
                      </button>
                    </>
                  ) : (
                    <button
                      type="button"
                      className="link-btn"
                      onClick={() => {
                        setEditingLabelFor(n.id);
                        setLabelInput(n.project_label ?? "");
                      }}
                    >
                      {n.project_label ? "Edit label" : "+ Project label"}
                    </button>
                  )}
                  <button
                    type="button"
                    className="link-btn link-btn-danger"
                    onClick={() => handleRemoveNumber(n.id)}
                    disabled={numberBusy}
                  >
                    Remove
                  </button>
                </li>
              ))}
            </ul>
            <div className="add-number-form">
              <input
                value={newNumber}
                onChange={(e) => setNewNumber(e.target.value)}
                placeholder="Add a number, e.g. 740052313"
              />
              <button type="button" className="btn btn-primary" onClick={handleAddNumber} disabled={numberBusy}>
                Add
              </button>
            </div>
            {numberError && <p className="form-error">{numberError}</p>}
          </div>
        )}

        {error && <p className="form-error">{error}</p>}

        <div className="panel-actions">
          <button type="button" className="btn btn-ghost" onClick={onCancel}>
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? "Saving…" : isEdit ? "Save changes" : "Add employee"}
          </button>
        </div>
      </form>
    </div>
  );
}