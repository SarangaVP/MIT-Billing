"""
One-time import: reads the 'Master sheet' from the Dialog Data Bucket
Excel export and seeds dialog_data_employees + dialog_data_connections.

CONFIRMED against the real file: an employee can hold MORE THAN ONE
connection (e.g. "Indusarani Silva" appears twice with 2 different
connection numbers, each billed separately at the full rate) — so rows
are grouped by EMP No first, then each row's connection number is added
under that one employee, mirroring Dialog Mobile's Employee/MobileNumber
structure, NOT Mobitel's simpler 1:1 model.

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


def main(xlsx_path: str):
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = wb["Master sheet"]

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    employees_inserted, connections_inserted = 0, 0
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
                employee = DialogDataEmployee(emp_no=emp_no_str, name=name_clean, team=team_clean)
                db.add(employee)
                db.flush()
                employee_by_emp_no[emp_no_str] = employee
                employees_inserted += 1

            db.add(DialogDataConnection(employee_id=employee.id, connection_no=connection_no_str))
            existing_connection_nos.add(connection_no_str)
            connections_inserted += 1

        db.commit()
    finally:
        db.close()

    print(f"Imported {employees_inserted} Dialog Data Bucket employees.")
    print(f"Imported {connections_inserted} connections (some employees have more than one).")
    print(f"Skipped {skipped_missing} rows with missing connection no/EMP No/name.")
    print(f"Skipped {skipped_duplicate_connection} duplicate connection numbers.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/import_dialog_data_master.py /path/to/file.xlsx")
        sys.exit(1)
    main(sys.argv[1])