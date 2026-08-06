"""
Parses the "Bill" sheet from the Dialog Data Bucket Excel export — per-
connection usage detail (Allocation/Usage/Remaining GB, Pay Go status).
Mirrors Mobitel's Portal parser. This is a monthly SNAPSHOT, matched to a
bill period's line items by mobile number — not written into employees.

NOTE: Allocation/Usage/Remaining GB are stored as raw strings, not
numbers — real data includes non-numeric values like "UNLIMITED" and
"NaN" (confirmed in the actual file), which would break a numeric column.
"""
import openpyxl


def _mobile_no_to_text(value) -> str:
    if isinstance(value, float):
        return str(int(value))
    return str(value)


def parse_bill_sheet(xlsx_path: str) -> dict:
    """Returns {mobile_no: {field: value, ...}}."""
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = wb["Bill"]

    result = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        mobile_no, name, allocation_gb, usage_gb, remaining_gb, pay_go_status, bill_cycle, update_time = row[:8]
        if mobile_no is None:
            continue

        result[_mobile_no_to_text(mobile_no)] = {
            "allocation_gb": str(allocation_gb) if allocation_gb is not None else None,
            "usage_gb": str(usage_gb) if usage_gb is not None else None,
            "remaining_gb": str(remaining_gb) if remaining_gb is not None else None,
            "pay_go_status": pay_go_status,
            "bill_cycle": bill_cycle,
        }

    return result