"""
One-time import: reads the 'Summary' sheet from the Mobitel data bucket
Excel export and seeds mobitel_employees.

Uses 'Summary', NOT 'Portal' — Portal lacks EMP No/LOB entirely.
Rows where EMP No is 'NA' and Name is 'Pool' are unassigned SIMs, skipped.

Usage:
    python scripts/import_mobitel_summary.py /path/to/Mobitel_Jun26.xlsx
"""
import sys
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.database import SessionLocal, Base, engine  # noqa: E402
from app.models.mobitel_employee import MobitelEmployee  # noqa: E402

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


def main(xlsx_path: str):
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = wb["Summary"]

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    inserted, skipped_pool, skipped_duplicate, skipped_missing = 0, 0, 0, 0

    try:
        existing_emp_nos = {e.emp_no for e in db.query(MobitelEmployee.emp_no).all()}

        for row in ws.iter_rows(min_row=2, max_row=1000, values_only=True):
            mobile_no, emp_no, name, lob = row[0], row[1], row[2], row[3]

            if mobile_no is None and emp_no is None and name is None:
                continue

            if is_pool_row(emp_no, name):
                skipped_pool += 1
                continue

            mobile_no, emp_no, name, lob = clean(mobile_no), clean(emp_no), clean(name), clean(lob)
            if not mobile_no or not emp_no or not name:
                skipped_missing += 1
                continue

            emp_no = str(emp_no)
            mobile_no = str(int(mobile_no)) if isinstance(mobile_no, float) else str(mobile_no)

            if emp_no in existing_emp_nos:
                skipped_duplicate += 1
                continue

            db.add(MobitelEmployee(emp_no=emp_no, name=name, mobile_no=mobile_no, lob=lob))
            existing_emp_nos.add(emp_no)
            inserted += 1

        db.commit()
    finally:
        db.close()

    print(f"Imported {inserted} Mobitel employees.")
    print(f"Skipped {skipped_pool} unassigned 'Pool' rows.")
    print(f"Skipped {skipped_missing} rows with missing EMP No/name/mobile no.")
    print(f"Skipped {skipped_duplicate} duplicate EMP Nos.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/import_mobitel_summary.py /path/to/file.xlsx")
        sys.exit(1)
    main(sys.argv[1])