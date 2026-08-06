"""
Parses the "Portal" sheet from the Mobitel data bucket Excel export — a raw
per-SIM technical export (IMSI, allocated/available/utilized data volume,
daily limits, member status). This is separate from the "Summary" sheet
(used for employee seeding) — Portal has no EMP No/LOB at all, only the
technical usage detail.

This is a monthly SNAPSHOT, not persistent employee data — matched to a
bill period's line items by mobile number, not written into mobitel_employees.
"""
import openpyxl

FIELD_INDEX = {
    "imsi_number": 0,
    "mobile_no": 3,
    "data_volume_mb": 4,
    "available_data_volume_mb": 6,
    "utilized_data_volume_mb": 7,
    "daily_limit_mb": 8,
    "utilized_daily_limit_mb": 9,
    "member_status": 10,
    "top_up_mb": 11,
    "utilized_topup_mb": 12,
}


def _mobile_no_to_text(value) -> str:
    if isinstance(value, float):
        return str(int(value))
    return str(value)


def parse_portal_sheet(xlsx_path: str) -> dict:
    """Returns {mobile_no: {field: value, ...}}, keyed for easy lookup at import time."""
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = wb["Portal"]

    result = {}
    for row in ws.iter_rows(min_row=3, values_only=True):
        if row[FIELD_INDEX["mobile_no"]] is None:
            continue

        mobile_no = _mobile_no_to_text(row[FIELD_INDEX["mobile_no"]])
        result[mobile_no] = {
            "imsi_number": str(row[FIELD_INDEX["imsi_number"]]) if row[FIELD_INDEX["imsi_number"]] is not None else None,
            "data_volume_mb": row[FIELD_INDEX["data_volume_mb"]],
            "available_data_volume_mb": row[FIELD_INDEX["available_data_volume_mb"]],
            "utilized_data_volume_mb": row[FIELD_INDEX["utilized_data_volume_mb"]],
            "daily_limit_mb": row[FIELD_INDEX["daily_limit_mb"]],
            "utilized_daily_limit_mb": row[FIELD_INDEX["utilized_daily_limit_mb"]],
            "member_status": row[FIELD_INDEX["member_status"]],
            "top_up_mb": row[FIELD_INDEX["top_up_mb"]],
            "utilized_topup_mb": row[FIELD_INDEX["utilized_topup_mb"]],
        }

    return result