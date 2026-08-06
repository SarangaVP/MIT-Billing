"""
One-time import: reads the 'Summary' sheet from the Mobitel data bucket
Excel export and seeds mobitel_employees.

Uses the 'Summary' sheet, NOT 'Portal' — Portal has richer SIM/usage detail
(IMSI, data volume, daily limits) but lacks EMP No and LOB entirely. Summary
already has Number/EMP No/Name/LOB, matching what we actually need.

Rows where EMP No is 'NA' and Name is 'Pool' are unassigned SIMs — real
lines held by no one, not employees. These ARE imported (for visibility —
so they show up in the Employees list rather than vanishing silently), with
a synthetic emp_no ("POOL-<mobile_no>", since the real EMP No is just the
literal text "NA" for every one of them and can't be used as-is — it isn't
unique) and status='pool'. The bill-splitting logic always excludes
status='pool' rows, same as it excludes 'inactive' — only 'active' rows are
ever billed.

Usage:
    python scripts/import_mobitel_summary.py /path/to/Mobitel_Jun26.xlsx
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


def main(xlsx_path: str):
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = wb["Summary"]

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    inserted, inserted_pool, skipped_duplicate, skipped_missing = 0, 0, 0, 0

    try:
        existing_emp_nos = {e.emp_no for e in db.query(MobitelEmployee.emp_no).all()}

        for row in ws.iter_rows(min_row=2, max_row=1000, values_only=True):
            mobile_no, emp_no, name, lob = row[0], row[1], row[2], row[3]

            if mobile_no is None and emp_no is None and name is None:
                continue  # blank filler row past the real data — not worth counting as "missing"

            mobile_no_clean, lob_clean = clean(mobile_no), clean(lob)
            mobile_no_str = str(int(mobile_no_clean)) if isinstance(mobile_no_clean, float) else str(mobile_no_clean)

            if is_pool_row(emp_no, name):
                if not mobile_no_str or mobile_no_str == "None":
                    skipped_missing += 1
                    continue
                synthetic_emp_no = f"POOL-{mobile_no_str}"
                if synthetic_emp_no in existing_emp_nos:
                    skipped_duplicate += 1
                    continue
                db.add(MobitelEmployee(
                    emp_no=synthetic_emp_no,
                    name="Pool",
                    mobile_no=mobile_no_str,
                    lob=lob_clean,
                    status=MobitelEmployeeStatus.pool,
                ))
                existing_emp_nos.add(synthetic_emp_no)
                inserted_pool += 1
                continue

            emp_no_clean, name_clean = clean(emp_no), clean(name)
            if not mobile_no_clean or not emp_no_clean or not name_clean:
                skipped_missing += 1
                continue

            emp_no_str = str(emp_no_clean)

            if emp_no_str in existing_emp_nos:
                skipped_duplicate += 1
                continue

            db.add(MobitelEmployee(emp_no=emp_no_str, name=name_clean, mobile_no=mobile_no_str, lob=lob_clean))
            existing_emp_nos.add(emp_no_str)
            inserted += 1

        db.commit()
    finally:
        db.close()

    print(f"Imported {inserted} real Mobitel employees.")
    print(f"Imported {inserted_pool} unassigned 'Pool' rows (status='pool', excluded from billing).")
    print(f"Skipped {skipped_missing} rows with missing EMP No/name/mobile no.")
    print(f"Skipped {skipped_duplicate} duplicate EMP Nos.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/import_mobitel_summary.py /path/to/file.xlsx")
        sys.exit(1)
    main(sys.argv[1])