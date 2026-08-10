"""
Syncs Dialog Data Bucket employees + connections from an uploaded Master
sheet, treating it as the full, authoritative current roster — same
"update in place, never delete" approach as employee_sheet_sync.py and
mobitel_sheet_sync.py (see either for why a real delete-and-replace
isn't safe: connections are referenced by past bills via a real foreign
key, and connection_no/EMP No have unique constraints that block reusing
an identifier even after a soft delete).

Shares its row-parsing logic (header-name column detection for the
newer/older LOB column formats, "0"/"#N/A" placeholder filtering) with
import_dialog_data_master.py.
"""
import openpyxl
from sqlalchemy.orm import Session

from app.models.dialog_data_employee import DialogDataEmployee
from app.models.dialog_data_connection import DialogDataConnection, DialogDataConnectionStatus


def clean(value):
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = value.replace("\ufeff", "").strip()
        return cleaned or None
    return value


def to_str(value) -> str | None:
    cleaned = clean(value)
    if cleaned is None:
        return None
    text = str(int(cleaned)) if isinstance(cleaned, float) else str(cleaned)
    if text in ("#N/A", "0"):
        return None
    return text


def _build_column_map(header_row) -> dict[str, int]:
    col_map = {}
    for idx, cell in enumerate(header_row):
        if cell is None:
            continue
        col_map[str(cell).strip().lower()] = idx
    return col_map


def _load_lob_codes_from_separate_sheet(wb) -> dict[str, str]:
    if "LOB" not in wb.sheetnames:
        return {}
    ws = wb["LOB"]
    codes: dict[str, str] = {}
    for row in ws.iter_rows(min_row=2, max_row=1000, values_only=True):
        emp_no = to_str(row[1]) if len(row) > 1 else None
        lob_code = to_str(row[7]) if len(row) > 7 else None
        if emp_no and lob_code:
            codes[emp_no] = lob_code
    return codes


def sync_dialog_data_sheet(db: Session, xlsx_path: str) -> dict:
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = wb["Master sheet"]

    header_row = next(ws.iter_rows(min_row=1, max_row=1, values_only=True))
    col_map = _build_column_map(header_row)

    connection_idx = col_map.get("connection no")
    emp_no_idx = col_map.get("emp no")
    name_idx = col_map.get("employee")
    team_idx = col_map.get("team")
    lob_idx = col_map.get("lob")

    has_lob_in_master = lob_idx is not None
    lob_codes_from_separate_sheet = {} if has_lob_in_master else _load_lob_codes_from_separate_sheet(wb)

    employee_by_emp_no: dict[str, DialogDataEmployee] = {e.emp_no: e for e in db.query(DialogDataEmployee).all()}
    connection_by_no: dict[str, DialogDataConnection] = {c.connection_no: c for c in db.query(DialogDataConnection).all()}

    grouped: dict[str, dict] = {}
    skipped_missing = 0

    for row in ws.iter_rows(min_row=2, max_row=1000, values_only=True):
        connection_no = row[connection_idx] if connection_idx is not None and connection_idx < len(row) else None
        emp_no = row[emp_no_idx] if emp_no_idx is not None and emp_no_idx < len(row) else None
        name = row[name_idx] if name_idx is not None and name_idx < len(row) else None
        team = row[team_idx] if team_idx is not None and team_idx < len(row) else None

        if connection_no is None and emp_no is None and name is None:
            continue

        connection_no_clean, emp_no_clean, name_clean, team_clean = clean(connection_no), clean(emp_no), clean(name), clean(team)
        if not connection_no_clean or not emp_no_clean or not name_clean:
            skipped_missing += 1
            continue

        connection_no_str = str(int(connection_no_clean)) if isinstance(connection_no_clean, float) else str(connection_no_clean)
        emp_no_str = str(emp_no_clean)

        lob_code = to_str(row[lob_idx]) if has_lob_in_master and lob_idx < len(row) else lob_codes_from_separate_sheet.get(emp_no_str)

        grouped.setdefault(emp_no_str, {"name": name_clean, "team": team_clean, "lob_code": lob_code, "connections": []})
        grouped[emp_no_str]["connections"].append(connection_no_str)

    emp_nos_in_upload = set(grouped.keys())
    inserted, updated, revived, retired_employees = 0, 0, 0, 0
    connections_added, connections_retired, connections_reactivated = 0, 0, 0
    conflicts: list[str] = []

    for emp_no, data in grouped.items():
        existing = employee_by_emp_no.get(emp_no)
        if existing is None:
            employee = DialogDataEmployee(emp_no=emp_no, name=data["name"], team=data["team"], lob_code=data["lob_code"])
            db.add(employee)
            db.flush()
            employee_by_emp_no[emp_no] = employee
            inserted += 1
        else:
            employee = existing
            was_deleted = employee.is_deleted
            employee.name = data["name"]
            employee.team = data["team"]
            if data["lob_code"]:
                employee.lob_code = data["lob_code"]
            employee.is_deleted = False
            if was_deleted:
                revived += 1
            else:
                updated += 1

        current_connections = {c.connection_no: c for c in db.query(DialogDataConnection).filter(DialogDataConnection.employee_id == employee.id).all()}
        new_connections = set(data["connections"])

        for connection_no in new_connections:
            conn = connection_by_no.get(connection_no)
            if conn is None:
                db.add(DialogDataConnection(employee_id=employee.id, connection_no=connection_no, status=DialogDataConnectionStatus.active))
                connections_added += 1
            elif conn.employee_id != employee.id:
                conflicts.append(f"{connection_no}: claimed by a different employee than EMP {emp_no}")
            elif conn.status != DialogDataConnectionStatus.active:
                conn.status = DialogDataConnectionStatus.active
                connections_reactivated += 1

        for connection_no, conn in current_connections.items():
            if connection_no not in new_connections and conn.status == DialogDataConnectionStatus.active:
                conn.status = DialogDataConnectionStatus.inactive
                connections_retired += 1

    for emp_no, employee in employee_by_emp_no.items():
        if emp_no not in emp_nos_in_upload and not employee.is_deleted:
            employee.is_deleted = True
            retired_employees += 1

    db.commit()

    return {
        "inserted_employees": inserted,
        "updated_employees": updated,
        "revived_employees": revived,
        "retired_employees": retired_employees,
        "connections_added": connections_added,
        "connections_retired": connections_retired,
        "connections_reactivated": connections_reactivated,
        "skipped_missing_rows": skipped_missing,
        "conflicts": conflicts,
        "lob_source": "directly in Master sheet" if has_lob_in_master else "separate LOB sheet (older format)",
    }