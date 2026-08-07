"""
One-time import (and re-run-safe refresh): reads the 'Summary' sheet from
the Mobitel data bucket Excel export and seeds/updates mobitel_employees.

IMPORTANT: reads columns by HEADER NAME, not fixed position. Confirmed
against real files that the column layout changes between exports — the
June'26 file had "LOB" holding the team NAME at column D; the July'26
file renamed that to "Team" and inserted a NEW "LOB" column at E holding
a numeric team CODE instead. Reading by position would have silently
misread the July file. Handles both:
  - If "Team" column exists (newer format): team name = Team, code = LOB
  - Else if only "LOB" exists (older format): team name = LOB, no code

Rows where EMP No is 'NA' and Name is 'Pool' are unassigned SIMs — real
lines held by no one, not employees. These ARE imported (for visibility),
with a synthetic emp_no ("POOL-<mobile_no>") and status='pool'.

Re-running this script with a newer file UPDATES existing employees'
team/lob_code (e.g. to backfill lob_code for people seeded before it
existed) — it does not just skip duplicates blindly.

Usage:
    python scripts/import_mobitel_summary.py /path/to/Mobitel_Jul26.xlsx
"""
import sys
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.database import SessionLocal, Base, engine  # noqa: E402
from app.models.mobitel_employee import MobitelEmployee, MobitelEmployeeStatus  # noqa: E402

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
    """Maps normalized header text -> column index, so we never rely on fixed positions."""
    col_map = {}
    for idx, cell in enumerate(header_row):
        if cell is None:
            continue
        key = str(cell).strip().lower()
        col_map[key] = idx
    return col_map


def main(xlsx_path: str):
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = wb["Summary"]

    header_row = next(ws.iter_rows(min_row=1, max_row=1, values_only=True))
    col_map = _build_column_map(header_row)

    mobile_idx = col_map.get("number")
    emp_no_idx = col_map.get("emp no")
    name_idx = col_map.get("name")
    team_idx = col_map.get("team")       # newer format: team NAME
    lob_idx = col_map.get("lob")          # older format: team NAME. newer format: numeric CODE
    has_team_column = team_idx is not None

    if mobile_idx is None or emp_no_idx is None or name_idx is None:
        print("ERROR: could not find 'Number'/'EMP No'/'Name' columns in the header row — check the file format.")
        print(f"Header found: {header_row}")
        sys.exit(1)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    inserted, inserted_pool, updated, skipped_missing, conflicts = 0, 0, 0, 0, 0
    conflict_details = []

    try:
        employee_by_emp_no: dict[str, MobitelEmployee] = {
            e.emp_no: e for e in db.query(MobitelEmployee).all()
        }
        employee_by_mobile: dict[str, MobitelEmployee] = {
            e.mobile_no: e for e in employee_by_emp_no.values()
        }

        for row in ws.iter_rows(min_row=2, max_row=1000, values_only=True):
            mobile_no = row[mobile_idx] if mobile_idx < len(row) else None
            emp_no = row[emp_no_idx] if emp_no_idx < len(row) else None
            name = row[name_idx] if name_idx < len(row) else None

            if mobile_no is None and emp_no is None and name is None:
                continue  # blank filler row past the real data

            mobile_no_str = to_str(mobile_no)

            if is_pool_row(emp_no, name):
                if not mobile_no_str:
                    skipped_missing += 1
                    continue
                synthetic_emp_no = f"POOL-{mobile_no_str}"
                if synthetic_emp_no in employee_by_emp_no:
                    continue  # already imported as a pool row

                conflicting_owner = employee_by_mobile.get(mobile_no_str)
                if conflicting_owner is not None:
                    # This number was a real employee's line before, now
                    # shows as unassigned "Pool" in this file — a genuine
                    # status change, not something to silently overwrite.
                    conflicts += 1
                    conflict_details.append(
                        f"  {mobile_no_str}: file shows this as unassigned 'Pool', but it's currently "
                        f"assigned to EMP {conflicting_owner.emp_no} ({conflicting_owner.name}) in our records"
                    )
                    continue

                employee = MobitelEmployee(
                    emp_no=synthetic_emp_no, name="Pool", mobile_no=mobile_no_str,
                    status=MobitelEmployeeStatus.pool,
                )
                db.add(employee)
                employee_by_emp_no[synthetic_emp_no] = employee
                employee_by_mobile[mobile_no_str] = employee
                inserted_pool += 1
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

            existing = employee_by_emp_no.get(emp_no_str)
            if existing is None:
                # This EMP No is new to us — but check whether this mobile
                # number is already claimed by a DIFFERENT existing
                # employee (confirmed real scenario: a number can be
                # reassigned to someone else between months). Don't guess
                # what to do — report it clearly instead of crashing or
                # silently overwriting someone else's record.
                conflicting_owner = employee_by_mobile.get(mobile_no_str)
                if conflicting_owner is not None:
                    conflicts += 1
                    conflict_details.append(
                        f"  {mobile_no_str}: file says EMP {emp_no_str} ({name_clean}), "
                        f"but already assigned to EMP {conflicting_owner.emp_no} ({conflicting_owner.name})"
                    )
                    continue

                employee = MobitelEmployee(
                    emp_no=emp_no_str, name=name_clean, mobile_no=mobile_no_str,
                    lob=team_name, lob_code=lob_code,
                )
                db.add(employee)
                employee_by_emp_no[emp_no_str] = employee
                employee_by_mobile[mobile_no_str] = employee
                inserted += 1
            else:
                # Refresh team/lob_code on re-import (e.g. to backfill
                # lob_code for people originally seeded from an older
                # file that didn't have this column).
                changed = False
                if team_name and existing.lob != team_name:
                    existing.lob = team_name
                    changed = True
                if lob_code and existing.lob_code != lob_code:
                    existing.lob_code = lob_code
                    changed = True
                if changed:
                    updated += 1

        db.commit()
    finally:
        db.close()

    print(f"Imported {inserted} new Mobitel employees.")
    print(f"Imported {inserted_pool} new unassigned 'Pool' rows.")
    print(f"Updated {updated} existing employees (team/lob_code refreshed).")
    print(f"Skipped {skipped_missing} rows with missing EMP No/name/mobile no.")
    if conflicts:
        print(f"CONFLICTS: {conflicts} mobile number(s) claimed by a different EMP No than currently on file:")
        for line in conflict_details:
            print(line)
        print("These were NOT imported — resolve manually (likely a genuine number reassignment).")
    print(f"File format: {'newer (Team name + numeric LOB code)' if has_team_column else 'older (LOB = team name only)'}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/import_mobitel_summary.py /path/to/file.xlsx")
        sys.exit(1)
    main(sys.argv[1])