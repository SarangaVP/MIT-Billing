"""
Parses the page-2-onward "Summary" table from a Dialog corporate bill PDF —
one row per mobile number, giving totals only (no Voice/SMS/Data breakdown).

Each summary row has 16 space-separated numeric fields after the mobile
number. Negative numbers and commas in figures are handled.
"""
import re

import pypdf

COLUMNS = [
    "mobile_no",
    "previous_due_amount",
    "payments",
    "total_usage_charges",
    "idd",
    "roaming",
    "vas",
    "discounts",
    "bill_adjustments_balance_transfers",
    "commitment_charges",
    "late_payment_charges",
    "add_to_bill_charges",
    "instalment_plans",
    "govt_taxes",
    "vat",
    "charges_for_bill_period",
    "total_due_amount",
]

# A summary row starts with a mobile/account number (7-10 digits), followed
# by 16 more numeric fields (each can be negative, have commas, decimals).
NUMBER_TOKEN = r"-?[\d,]+\.\d{2}"
ROW_PATTERN = re.compile(
    r"^(\d{7,10})\s+" + r"\s+".join([NUMBER_TOKEN] * 16) + r"$"
)


def _to_float(token: str) -> float:
    return float(token.replace(",", ""))


def find_summary_page_range(pdf_path: str) -> tuple[int, int]:
    """Returns (start_page_index, end_page_index_exclusive) for the summary table."""
    reader = pypdf.PdfReader(pdf_path)
    start = None
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        is_summary_header_page = "MOBILE/" in text and "ACCOUNT" in text and "NUMBER" in text
        is_detail_page = "MOBILE NUMBER:" in text and "INVOICE" in text

        if start is None and is_summary_header_page:
            start = i
        elif start is not None and is_detail_page:
            return start, i
    if start is not None:
        return start, len(reader.pages)
    raise ValueError("Could not locate the summary table in this PDF")


def extract_cover_page_totals(pdf_path: str) -> dict:
    """
    Extracts the invoice-level metadata and stated grand totals from the
    cover page (page 0) — used to reconcile against the sum of parsed line
    items, so an import that doesn't add up is caught immediately.
    """
    reader = pypdf.PdfReader(pdf_path)
    text = reader.pages[0].extract_text() or ""

    def find(pattern, cast=str):
        m = re.search(pattern, text)
        if not m:
            return None
        val = m.group(1).replace(",", "")
        return cast(val)

    corporate_code = find(r"CORPORATE CODE:\s*([A-Z0-9]+)")
    bill_period = re.search(r"BILL PERIOD:\s*(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})", text)
    invoice_date = find(r"Date of Invoice\s*:\s*(\d{2}/\d{2}/\d{4})")
    total_charges = find(r"Total Charges for Bill\s+([\d,]+\.\d{2})", float)
    total_due = find(r"Total Due\s+([\d,]+\.\d{2})", float)

    return {
        "corporate_code": corporate_code,
        "bill_period_start": bill_period.group(1) if bill_period else None,
        "bill_period_end": bill_period.group(2) if bill_period else None,
        "invoice_date": invoice_date,
        "stated_total_charges_for_bill_period": total_charges,
        "stated_total_due_amount": total_due,
    }


def parse_summary_table(pdf_path: str) -> list[dict]:
    reader = pypdf.PdfReader(pdf_path)
    start, end = find_summary_page_range(pdf_path)

    rows = []
    unparsed_lines = []

    for i in range(start, end):
        text = reader.pages[i].extract_text() or ""
        for line in text.split("\n"):
            line = line.strip()
            match = ROW_PATTERN.match(line)
            if not match:
                continue

            mobile_no = match.group(1)
            numbers = re.findall(NUMBER_TOKEN, line)
            if len(numbers) != 16:
                unparsed_lines.append(line)
                continue

            row = {"mobile_no": mobile_no}
            for col, val in zip(COLUMNS[1:], numbers):
                row[col] = _to_float(val)
            rows.append(row)

    return rows