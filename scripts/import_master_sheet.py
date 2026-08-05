"""
One-time import: reads the 'Master sheet' tab from the existing manually
maintained Excel file and loads it into employees + mobile_numbers.

The sheet actually contains TWO tables stacked on top of each other:

  1. The main employee list (row 1 header: Mobile No | EMP No | Name | LOB |
     Cadre | Credit Limit | Level | Email | Resignation | ...)

  2. A second block, labeled "Additional common connection", listing extra
     mobile numbers for EMP Nos that already exist in table 1 — but its
     columns are SHIFTED one position to the right compared to table 1:
         (blank) | Mobile No | EMP No | Name | LOB | Cadre

Some EMP Nos in table 2 are the literal text "General" — pooled/shared
lines (security post phones, a shared data bucket) not tied to one named
person. These are SET ASIDE for now, not imported, reported separately.

Some employees in table 1 have a placeholder like "No" instead of a real
mobile number — meaning the employee genuinely has no company mobile
number assigned. They're still imported as employees, with zero numbers.

The Resignation column (usually "No", sometimes a date in varying formats)
is imported as-is into employees.resignation as plain text — it is not
parsed into a structured status/date.

Only a truly empty cell is converted to NULL. Stray invisible BOM
characters (a copy-paste artifact seen in ~49 names) are stripped, since
they carry no real information and only cause display/search bugs.
Everything else — including literal "#N/A" text, 0s — is imported as-is.

Usage:
    python scripts/import_master_sheet.py /path/to/Mobile_bill_July_26.xlsx
"""
import sys
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.database import SessionLocal, Base, engine  # noqa: E402
from app.models.employee import Employee  # noqa: E402
from app.models.mobile_number import MobileNumber  # noqa: E402

ADDITIONAL_BLOCK_MARKER = "Additional common connection"
UNRESOLVED_EMP_NO_PLACEHOLDERS = {"General"}
NO_NUMBER_ASSIGNED_PLACEHOLDERS = {"no", "none", "n/a", "na", "tbc", "pending", "-"}


def is_no_number_placeholder(value) -> bool:
    return isinstance(value, str) and value.strip().lower() in NO_NUMBER_ASSIGNED_PLACEHOLDERS


def clean(value):
    """Converts a truly empty cell to None, and strips invisible BOM
    characters (U+FEFF) that appear stuck in some names from copy-pasting.
    Everything else is left exactly as-is."""
    if value is None:
        return None
    if isinstance(value, str):
        value = value.replace("\ufeff", "")
        if value.strip() == "":
            return None
    return value


def to_text(value):
    if value is None:
        return None
    return str(value)


def load_raw_rows(xlsx_path: str):
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = wb["Master sheet"]
    return [list(row) for row in ws.iter_rows(min_row=1, max_row=ws.max_row, values_only=True)]


def find_marker_row_index(rows, marker_text):
    for i, row in enumerate(rows):
        for cell in row:
            if isinstance(cell, str) and cell.strip() == marker_text:
                return i
    return None


def main(xlsx_path: str):
    rows = load_raw_rows(xlsx_path)
    marker_idx = find_marker_row_index(rows, ADDITIONAL_BLOCK_MARKER)

    main_rows = rows[1:marker_idx] if marker_idx is not None else rows[1:]
    additional_rows = rows[marker_idx + 1:] if marker_idx is not None else []

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    inserted_employees, inserted_numbers = 0, 0
    skipped_missing = 0
    skipped_duplicate_employees = 0
    duplicate_number_details = []
    unresolved_placeholder_rows = []
    unmatched_additional_rows = []
    no_number_employees = []

    try:
        existing_emp_nos = {e.emp_no for e in db.query(Employee.emp_no).all()}
        existing_mobile_nos = {m.mobile_no for m in db.query(MobileNumber.mobile_no).all()}
        emp_no_to_employee_id = {e.emp_no: e.id for e in db.query(Employee.id, Employee.emp_no).all()}

        # ---- Table 1: main employee list ----
        # Column order: Mobile No, EMP No, Name, LOB, Cadre, Credit Limit, Level, Email, Resignation
        grouped = {}
        for row in main_rows:
            raw_mobile_no = clean(row[0] if len(row) > 0 else None)
            emp_no = to_text(clean(row[1] if len(row) > 1 else None))

            if not emp_no:
                skipped_missing += 1
                continue

            grouped.setdefault(emp_no, {"rows": [], "first": row})

            if raw_mobile_no is None:
                skipped_missing += 1
                continue

            if is_no_number_placeholder(raw_mobile_no):
                continue

            grouped[emp_no]["rows"].append(to_text(raw_mobile_no))

        for emp_no, data in grouped.items():
            if emp_no in existing_emp_nos:
                skipped_duplicate_employees += 1
                continue

            first_row = data["first"]
            employee = Employee(
                emp_no=emp_no,
                name=clean(first_row[2] if len(first_row) > 2 else None),
                lob=clean(first_row[3] if len(first_row) > 3 else None),
                cadre=clean(first_row[4] if len(first_row) > 4 else None),
                credit_limit=clean(first_row[5] if len(first_row) > 5 else None),
                level=clean(first_row[6] if len(first_row) > 6 else None),
                email=clean(first_row[7] if len(first_row) > 7 else None),
                resignation=clean(first_row[8] if len(first_row) > 8 else None),
            )
            db.add(employee)
            db.flush()
            inserted_employees += 1
            emp_no_to_employee_id[emp_no] = employee.id

            if not data["rows"]:
                no_number_employees.append((emp_no, employee.name))

            for i, mobile_no in enumerate(dict.fromkeys(data["rows"])):
                if mobile_no in existing_mobile_nos:
                    duplicate_number_details.append((emp_no, mobile_no, "already used elsewhere"))
                    continue
                db.add(MobileNumber(employee_id=employee.id, mobile_no=mobile_no, is_primary=(i == 0)))
                existing_mobile_nos.add(mobile_no)
                inserted_numbers += 1

        # ---- Table 2: "Additional common connection" (shifted columns) ----
        for row in additional_rows:
            mobile_no = to_text(clean(row[1] if len(row) > 1 else None))
            emp_no = to_text(clean(row[2] if len(row) > 2 else None))

            if not mobile_no or not emp_no:
                continue

            if emp_no in UNRESOLVED_EMP_NO_PLACEHOLDERS:
                unresolved_placeholder_rows.append((mobile_no, emp_no, clean(row[3] if len(row) > 3 else None)))
                continue

            employee_id = emp_no_to_employee_id.get(emp_no)
            if not employee_id:
                unmatched_additional_rows.append((mobile_no, emp_no))
                continue

            if mobile_no in existing_mobile_nos:
                duplicate_number_details.append((emp_no, mobile_no, "already used elsewhere"))
                continue

            db.add(MobileNumber(employee_id=employee_id, mobile_no=mobile_no, is_primary=False))
            existing_mobile_nos.add(mobile_no)
            inserted_numbers += 1

        db.commit()
    finally:
        db.close()

    print(f"Imported {inserted_employees} employees with {inserted_numbers} mobile numbers total.")
    print(f"Skipped {skipped_missing} rows with missing EMP No or mobile no.")
    print(f"Skipped {skipped_duplicate_employees} EMP Nos that already existed in the database.")

    if duplicate_number_details:
        print(f"\n{len(duplicate_number_details)} mobile number(s) could not be attached (already claimed elsewhere):")
        for emp_no, mobile_no, reason in duplicate_number_details:
            print(f"  - {mobile_no} for EMP No {emp_no} ({reason})")

    if unmatched_additional_rows:
        print(f"\n{len(unmatched_additional_rows)} row(s) in 'Additional common connection' referenced an EMP No not found anywhere:")
        for mobile_no, emp_no in unmatched_additional_rows:
            print(f"  - {mobile_no} -> EMP No {emp_no}")

    if unresolved_placeholder_rows:
        print(f"\n{len(unresolved_placeholder_rows)} row(s) SET ASIDE (EMP No is a placeholder like 'General', not a real employee) — decide how to handle these later:")
        for mobile_no, emp_no, label in unresolved_placeholder_rows:
            print(f"  - {mobile_no} (EMP No: {emp_no}, label: {label})")

    if no_number_employees:
        print(f"\n{len(no_number_employees)} employee(s) imported with NO mobile number (source sheet had a placeholder like 'No'):")
        for emp_no, name in no_number_employees:
            print(f"  - {name} (EMP No: {emp_no})")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/import_master_sheet.py /path/to/file.xlsx")
        sys.exit(1)
    main(sys.argv[1])