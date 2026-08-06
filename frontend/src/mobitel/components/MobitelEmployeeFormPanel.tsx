import { useState, type FormEvent } from "react";
import type { MobitelEmployee, MobitelEmployeeCreateInput, MobitelEmployeeUpdateInput } from "../types/mobitel";

interface Props {
  employee: MobitelEmployee | null;
  onSave: (payload: MobitelEmployeeCreateInput | MobitelEmployeeUpdateInput) => Promise<void>;
  onCancel: () => void;
}

interface FormState {
  emp_no: string;
  name: string;
  mobile_no: string;
  lob: string;
  status: "active" | "inactive";
}

const EMPTY: FormState = { emp_no: "", name: "", mobile_no: "", lob: "", status: "active" };

export default function MobitelEmployeeFormPanel({ employee, onSave, onCancel }: Props) {
  const isEdit = employee !== null;
  const [form, setForm] = useState<FormState>(
    employee
      ? {
          emp_no: employee.emp_no,
          name: employee.name,
          mobile_no: employee.mobile_no,
          lob: employee.lob ?? "",
          status: employee.status,
        }
      : EMPTY
  );
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  function update<K extends keyof FormState>(field: K, value: FormState[K]) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      const payload = {
        emp_no: form.emp_no,
        name: form.name,
        mobile_no: form.mobile_no,
        lob: form.lob || null,
        ...(isEdit ? { status: form.status } : {}),
      };
      await onSave(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="panel-overlay" onClick={onCancel}>
      <form className="panel" onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
        <h2>{isEdit ? "Edit Mobitel employee" : "Add Mobitel employee"}</h2>

        <label>
          EMP No
          <input required disabled={isEdit} value={form.emp_no} onChange={(e) => update("emp_no", e.target.value)} />
        </label>

        <label>
          Name
          <input required value={form.name} onChange={(e) => update("name", e.target.value)} />
        </label>

        <label>
          Mobile No
          <input required value={form.mobile_no} onChange={(e) => update("mobile_no", e.target.value)} />
        </label>

        <label>
          LOB
          <input value={form.lob} onChange={(e) => update("lob", e.target.value)} />
        </label>

        {isEdit && (
          <label>
            Status
            <select value={form.status} onChange={(e) => update("status", e.target.value as "active" | "inactive")}>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
            <span className="field-hint">Inactive employees are excluded from the next bill split.</span>
          </label>
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