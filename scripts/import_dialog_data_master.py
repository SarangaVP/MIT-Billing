"""
One-time import: reads the 'Master sheet' from the Dialog Data Bucket
Excel export and seeds dialog_data_employees + dialog_data_connections.
Also reads the SEPARATE 'LOB' sheet (an org-chart/HR export, keyed by
EMP No) to backfill each employee's numeric lob_code.

CONFIRMED against the real file: an employee can hold MORE THAN ONE
connection (e.g. "Indusarani Silva" appears twice with 2 different
connection numbers, each billed separately at the full rate) — so rows
are grouped by EMP No first, then each row's connection number is added
under that one employee, mirroring Dialog Mobile's Employee/MobileNumber
structure, NOT Mobitel's simpler 1:1 model.

CONFIRMED the 'LOB' sheet has TWO columns both literally named "LOB" —
the first has 33 rows with a literal "#N/A" error string, the second has
zero errors. Uses the second one. Coverage is ~95% (467/489 employees) —
people with no matching row in this sheet simply get lob_code=None.

Usage:
    python scripts/import_dialog_data_master.py /path/to/Dialog_data_Jul26.xlsx
"""
import sys
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.database import SessionLocal, Base, engine  # noqa: E402
from app.models.dialog_data_employee import DialogDataEmployee  # noqa: E402
from app.models.dialog_data_connection import DialogDataConnection  # noqa: E402


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
    if str(cleaned) == "#N/A":
        return None
    return str(int(cleaned)) if isinstance(cleaned, float) else str(cleaned)


def _load_lob_codes(wb) -> dict[str, str]:
    """Returns {emp_no: lob_code} from the 'LOB' sheet, keyed by EMP No."""
    if "LOB" not in wb.sheetnames:
        return {}
    ws = wb["LOB"]
    codes: dict[str, str] = {}
    for row in ws.iter_rows(min_row=2, max_row=1000, values_only=True):
        emp_no = to_str(row[1]) if len(row) > 1 else None
        lob_code = to_str(row[7]) if len(row) > 7 else None  # second "LOB" column — the reliable one
        if emp_no and lob_code:
            codes[emp_no] = lob_code
    return codes


def main(xlsx_path: str):
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = wb["Master sheet"]
    lob_codes = _load_lob_codes(wb)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    employees_inserted, connections_inserted, lob_codes_backfilled = 0, 0, 0
    skipped_missing, skipped_duplicate_connection = 0, 0

    try:
        employee_by_emp_no: dict[str, DialogDataEmployee] = {
            e.emp_no: e for e in db.query(DialogDataEmployee).all()
        }
        existing_connection_nos = {
            c.connection_no for c in db.query(DialogDataConnection).all()
        }

        for row in ws.iter_rows(min_row=2, max_row=1000, values_only=True):
            connection_no, emp_no, name, team = row[0], row[1], row[2], row[3]

            if connection_no is None and emp_no is None and name is None:
                continue

            connection_no_clean, emp_no_clean, name_clean, team_clean = (
                clean(connection_no), clean(emp_no), clean(name), clean(team)
            )
            if not connection_no_clean or not emp_no_clean or not name_clean:
                skipped_missing += 1
                continue

            connection_no_str = (
                str(int(connection_no_clean)) if isinstance(connection_no_clean, float) else str(connection_no_clean)
            )
            emp_no_str = str(emp_no_clean)

            if connection_no_str in existing_connection_nos:
                skipped_duplicate_connection += 1
                continue

            employee = employee_by_emp_no.get(emp_no_str)
            if employee is None:
                employee = DialogDataEmployee(
                    emp_no=emp_no_str, name=name_clean, team=team_clean,
                    lob_code=lob_codes.get(emp_no_str),
                )
                db.add(employee)
                db.flush()
                employee_by_emp_no[emp_no_str] = employee
                employees_inserted += 1
                if employee.lob_code:
                    lob_codes_backfilled += 1
            elif employee.lob_code is None and emp_no_str in lob_codes:
                # Backfill lob_code for an employee already seeded before
                # this field existed, or before we had the LOB sheet.
                employee.lob_code = lob_codes[emp_no_str]
                lob_codes_backfilled += 1

            db.add(DialogDataConnection(employee_id=employee.id, connection_no=connection_no_str))
            existing_connection_nos.add(connection_no_str)
            connections_inserted += 1

        db.commit()
    finally:
        db.close()

    print(f"Imported {employees_inserted} Dialog Data Bucket employees.")
    print(f"Imported {connections_inserted} connections (some employees have more than one).")
    print(f"Backfilled lob_code for {lob_codes_backfilled} employees ({len(lob_codes)} available in the LOB sheet).")
    print(f"Skipped {skipped_missing} rows with missing connection no/EMP No/name.")
    print(f"Skipped {skipped_duplicate_connection} duplicate connection numbers.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/import_dialog_data_master.py /path/to/file.xlsx")
        sys.exit(1)
    main(sys.argv[1])