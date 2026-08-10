"""
Syncs Mobitel employees + connections from an uploaded Summary sheet,
treating it as the full, authoritative current roster — same "update in
place, never delete" approach as employee_sheet_sync.py (see that
module's docstring for why a real delete-and-replace isn't safe here:
connections are referenced by past bills via a real foreign key, and
mobile_no/emp_no have unique constraints that block reusing an
identifier even after a soft delete).

Shares its row-parsing logic (header-name column detection for the
Team/LOB column format change, Pool row handling) with
import_mobitel_summary.py.
"""
import openpyxl
from sqlalchemy.orm import Session

from app.models.mobitel_employee import MobitelEmployee
from app.models.mobitel_connection import MobitelConnection, MobitelConnectionStatus

POOL_MARKERS = {"na", "pool"}


def is_pool_row(emp_no, name) -> bool:
    return (str(emp_no).strip().lower() in POOL_MARKERS) or (str(name).strip().lower() == "pool")


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
    return str(int(cleaned)) if isinstance(cleaned, float) else str(cleaned)


def _build_column_map(header_row) -> dict[str, int]:
    col_map = {}
    for idx, cell in enumerate(header_row):
        if cell is None:
            continue
        col_map[str(cell).strip().lower()] = idx
    return col_map


def sync_mobitel_sheet(db: Session, xlsx_path: str) -> dict:
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = wb["Summary"]

    header_row = next(ws.iter_rows(min_row=1, max_row=1, values_only=True))
    col_map = _build_column_map(header_row)

    mobile_idx = col_map.get("number")
    emp_no_idx = col_map.get("emp no")
    name_idx = col_map.get("name")
    team_idx = col_map.get("team")
    lob_idx = col_map.get("lob")
    has_team_column = team_idx is not None

    if mobile_idx is None or emp_no_idx is None or name_idx is None:
        raise ValueError("Could not find 'Number'/'EMP No'/'Name' columns in the header row.")

    employee_by_emp_no: dict[str, MobitelEmployee] = {e.emp_no: e for e in db.query(MobitelEmployee).all()}
    connection_by_mobile: dict[str, MobitelConnection] = {c.mobile_no: c for c in db.query(MobitelConnection).all()}

    grouped: dict[str, dict] = {}
    pool_rows: list[tuple[str, str]] = []   # (mobile_no, synthetic_emp_no)
    skipped_missing = 0

    for row in ws.iter_rows(min_row=2, max_row=1000, values_only=True):
        mobile_no = row[mobile_idx] if mobile_idx < len(row) else None
        emp_no = row[emp_no_idx] if emp_no_idx < len(row) else None
        name = row[name_idx] if name_idx < len(row) else None

        if mobile_no is None and emp_no is None and name is None:
            continue

        mobile_no_str = to_str(mobile_no)

        if is_pool_row(emp_no, name):
            if not mobile_no_str:
                skipped_missing += 1
                continue
            pool_rows.append((mobile_no_str, f"POOL-{mobile_no_str}"))
            continue

        emp_no_str, name_clean = to_str(emp_no), clean(name)
        if not mobile_no_str or not emp_no_str or not name_clean:
            skipped_missing += 1
            continue

        if has_team_column:
            team_name = clean(row[team_idx]) if team_idx < len(row) else None
            lob_code = to_str(row[lob_idx]) if lob_idx is not None and lob_idx < len(row) else None
        else:
            team_name = clean(row[lob_idx]) if lob_idx is not None and lob_idx < len(row) else None
            lob_code = None

        grouped.setdefault(emp_no_str, {"name": name_clean, "team": team_name, "lob_code": lob_code, "mobiles": []})
        grouped[emp_no_str]["mobiles"].append(mobile_no_str)

    emp_nos_in_upload = set(grouped.keys()) | {syn for _, syn in pool_rows}
    inserted, updated, revived, retired_employees = 0, 0, 0, 0
    connections_added, connections_retired, connections_reactivated = 0, 0, 0
    conflicts: list[str] = []

    for emp_no, data in grouped.items():
        existing = employee_by_emp_no.get(emp_no)
        if existing is None:
            employee = MobitelEmployee(
                emp_no=emp_no, name=data["name"], lob=data["team"], lob_code=data["lob_code"], is_pool=False,
            )
            db.add(employee)
            db.flush()
            employee_by_emp_no[emp_no] = employee
            inserted += 1
        else:
            employee = existing
            was_deleted = employee.is_deleted
            employee.name = data["name"]
            employee.lob = data["team"]
            if data["lob_code"]:
                employee.lob_code = data["lob_code"]
            employee.is_deleted = False
            employee.is_pool = False
            if was_deleted:
                revived += 1
            else:
                updated += 1

        current_mobiles = {c.mobile_no: c for c in db.query(MobitelConnection).filter(MobitelConnection.employee_id == employee.id).all()}
        new_mobiles = set(data["mobiles"])

        for mobile_no in new_mobiles:
            conn = connection_by_mobile.get(mobile_no)
            if conn is None:
                db.add(MobitelConnection(employee_id=employee.id, mobile_no=mobile_no, status=MobitelConnectionStatus.active))
                connections_added += 1
            elif conn.employee_id != employee.id:
                conflicts.append(f"{mobile_no}: claimed by a different employee than EMP {emp_no}")
            elif conn.status != MobitelConnectionStatus.active:
                conn.status = MobitelConnectionStatus.active
                connections_reactivated += 1

        for mobile_no, conn in current_mobiles.items():
            if mobile_no not in new_mobiles and conn.status == MobitelConnectionStatus.active:
                conn.status = MobitelConnectionStatus.inactive
                connections_retired += 1

    for mobile_no, synthetic_emp_no in pool_rows:
        existing_conn = connection_by_mobile.get(mobile_no)
        if existing_conn is not None and existing_conn.employee_id in {e.id for e in employee_by_emp_no.values() if not e.is_pool}:
            # This number belonged to a REAL employee before and is now
            # showing as unassigned "Pool" — a genuine status change, not
            # something to silently reassign or drop. Confirmed real case:
            # this is exactly how one of the 4 known real reassignment
            # conflicts actually happens (705329362: was Isuru Hasanka's
            # number in June, "NA"/Pool in July).
            owner = next((e for e in employee_by_emp_no.values() if e.id == existing_conn.employee_id), None)
            conflicts.append(
                f"{mobile_no}: file shows this as unassigned 'Pool', but it's currently assigned to "
                f"EMP {owner.emp_no if owner else '?'} ({owner.name if owner else '?'})"
            )
            continue

        existing = employee_by_emp_no.get(synthetic_emp_no)
        if existing is None:
            employee = MobitelEmployee(emp_no=synthetic_emp_no, name="Pool", is_pool=True)
            db.add(employee)
            db.flush()
            employee_by_emp_no[synthetic_emp_no] = employee
            if existing_conn is None:
                db.add(MobitelConnection(employee_id=employee.id, mobile_no=mobile_no))
                connections_added += 1
            inserted += 1
        else:
            was_deleted = existing.is_deleted
            existing.is_deleted = False
            if was_deleted:
                revived += 1

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
        "file_format": "newer (Team name + numeric LOB code)" if has_team_column else "older (LOB = team name only)",
    }