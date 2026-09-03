"""
Parses the "Invoice" sheet from Dialog's .xls bill export — a structurally
simpler source than the PDF, since it's a real spreadsheet with a fixed
table rather than a printed document split across pages.

Confirmed against a real bill: this export OMITS some dormant/zero-activity
accounts that the PDF still lists (accounts with only a carried-over
previous-due balance and no current-period charges). This means the sum of
line items from this file can legitimately fall slightly short of the
invoice's own stated total — that's expected, not a parsing bug — so
reconciliation for this source is relaxed (see bill_service.py), not
strict like the PDF path.

Requires the 'xlrd' package — this is an old binary .xls format, which
openpyxl cannot read at all.
"""
import xlrd

HEADER_MARKER = "Mobile No"

FIELD_MAP = {
    "Previous Due Amount": "previous_due_amount",
    "Payment": "payments",
    "Total Usage Charges": "total_usage_charges",
    "Voice Rental": "voice_rental",
    "Voice Usage": "voice_usage",
    "SMS": "sms",
    "Data Rental": "data_rental",
    "Data Usage": "data_usage",
    "IDD": "idd",
    "Roaming": "roaming",
    "VAS": "vas",
    "Discounts/Bill Adjustments": "discounts",
    "Balance Adjustments": "bill_adjustments_balance_transfers",
    "Commitment Charges": "commitment_charges",
    "Late Payment Charges": "late_payment_charges",
    "Add to Bill Charges": "add_to_bill_charges",
    "Installment Plans (NON TAX)": "instalment_plans",
    "Government Taxes": "govt_taxes",
    "VAT": "vat",
    "Charges for Bill Period": "charges_for_bill_period",
    "Total Amount Payable": "total_due_amount",
}

COVER_LABELS = {
    "CORPORATE CODE": "corporate_code",
    "Bill Period": "bill_period",
    "INVOICE DATE": "invoice_date",
    "Total Charges for Bill Period": "stated_total_charges_for_bill_period",
    "Total Amount Payable": "stated_total_due_amount",
}


def _normalize_header(value) -> str:
    """Same normalization used everywhere else in this project for header
    matching (dialog_mobile_sheet_sync.py, dialog_data_sheet_sync.py,
    mobitel_sheet_sync.py) — strip whitespace, lowercase. Applying it here
    too closes a real gap: this file previously matched header text with
    a bare `==`, which would silently mis-parse (see below) on a stray
    space or case change in Dialog's own export, exactly the class of bug
    already confirmed and fixed for Cadre/LOB text elsewhere."""
    if value is None:
        return ""
    return str(value).strip().lower()


def _mobile_no_to_text(value) -> str:
    if isinstance(value, float):
        return str(int(value))
    return str(value)


def find_header_row(sheet) -> int:
    """
    Searches every row (the cover page before this can run well past 10
    rows, so there's no fixed cap here) for a row that CONTAINS the
    normalized "Mobile No" marker anywhere in it — not fixed to column 0.
    Confirmed real risk this replaces: matching only column 0 with a bare
    `==` would break outright on a harmless column reordering or a
    trailing-space export quirk, even though the header row itself would
    still be perfectly readable by a human looking at the file.
    """
    marker = _normalize_header(HEADER_MARKER)
    for r in range(sheet.nrows):
        row_values = [_normalize_header(v) for v in sheet.row_values(r)]
        if marker in row_values:
            return r
    raise ValueError(f"Could not find the '{HEADER_MARKER}' header row in this .xls file")


def extract_cover_totals(sheet) -> dict:
    values = {}
    for r in range(sheet.nrows):
        label = sheet.cell_value(r, 0)
        if label in COVER_LABELS:
            values[COVER_LABELS[label]] = sheet.cell_value(r, 1)

    bill_period_start = bill_period_end = None
    if values.get("bill_period"):
        parts = str(values["bill_period"]).split("-")
        if len(parts) == 2:
            bill_period_start, bill_period_end = parts[0].strip(), parts[1].strip()

    return {
        "corporate_code": values.get("corporate_code"),
        "bill_period_start": bill_period_start,
        "bill_period_end": bill_period_end,
        "invoice_date": values.get("invoice_date"),
        "stated_total_charges_for_bill_period": values.get("stated_total_charges_for_bill_period"),
        "stated_total_due_amount": values.get("stated_total_due_amount"),
    }


def parse_summary_table(xls_path: str) -> list[dict]:
    wb = xlrd.open_workbook(xls_path)
    sheet = wb.sheet_by_name("Invoice")

    header_row = find_header_row(sheet)
    header = sheet.row_values(header_row)

    # Normalized lookup: every FIELD_MAP key (plus the Mobile No marker
    # itself) matched against the ACTUAL header text via the same
    # strip+lowercase normalization used for the header ROW search above,
    # instead of the previous bare `==`. This still closes a real gap —
    # a trailing space or case change on a column header no longer
    # silently drops that column — while deliberately NOT requiring every
    # column to be present (see below): Dialog's own export format can
    # legitimately change between months.
    normalized_field_map = {_normalize_header(k): v for k, v in FIELD_MAP.items()}
    normalized_mobile_marker = _normalize_header(HEADER_MARKER)

    col_index: dict[str, int] = {}
    for i, name in enumerate(header):
        normalized = _normalize_header(name)
        if normalized == normalized_mobile_marker:
            col_index["Mobile No"] = i
        elif normalized in normalized_field_map:
            # Map back to the FIELD_MAP's own original key so the rest of
            # this function (which still keys off FIELD_MAP.items()) is
            # unchanged below.
            original_key = next(k for k in FIELD_MAP if _normalize_header(k) == normalized)
            col_index[original_key] = i

    if "Mobile No" not in col_index:
        raise ValueError("Found a header row, but could not locate the 'Mobile No' column within it")

    # Deliberately NOT a hard requirement that every FIELD_MAP column be
    # present: Dialog's own export format can genuinely add/rename/drop
    # columns between months, and a missing optional field should degrade
    # gracefully (that column's value falls back to 0 downstream via
    # row.get(field_name, 0) in the bill service) rather than blocking
    # the whole import. Only Mobile No — the one column every single row
    # depends on to exist at all — is a hard requirement.

    rows = []
    for r in range(header_row + 1, sheet.nrows):
        mobile_no = sheet.cell_value(r, col_index["Mobile No"])
        if not mobile_no:
            continue

        row = {"mobile_no": _mobile_no_to_text(mobile_no)}
        for header_name, field_name in FIELD_MAP.items():
            if header_name in col_index:
                val = sheet.cell_value(r, col_index[header_name])
                row[field_name] = float(val) if val != "" else 0.0
        rows.append(row)

    return rows


def extract_cover_page_totals(xls_path: str) -> dict:
    wb = xlrd.open_workbook(xls_path)
    sheet = wb.sheet_by_name("Invoice")
    return extract_cover_totals(sheet)