"""
Parses a single-page SLT Mobitel corporate bill PDF. Unlike Dialog, this
bill has NO per-employee breakdown at all — just company-wide totals.

The PDF's header block gets badly scrambled by text extraction. The
"Account Summary" section extracts cleanly line-by-line, so the actual
financial figures come from there.

CRITICAL: filler dots must be matched with \\.{3,} (3+ dots), not \\.+ —
some labels contain their own decimal point (e.g. "Cess (2%) (Eff 2.04%)")
which \\.+ would incorrectly latch onto instead of the real filler run.
"""
import re

import pypdf


def _find(text: str, pattern: str, cast=str):
    m = re.search(pattern, text, re.DOTALL)
    if not m:
        return None
    val = m.group(1).replace(",", "")
    return cast(val)


def parse_mobitel_bill(pdf_path: str) -> dict:
    reader = pypdf.PdfReader(pdf_path)
    text = reader.pages[0].extract_text() or ""

    bill_date = _find(text, r"Bill Date\s+(\d{2}/\d{2}/\d{4})")
    account_no = _find(text, r"Colombo\s*\d+\s*\n(\d{6,10})")
    bill_no = _find(text, r"Bill Date\s+\d{2}/\d{2}/\d{4}\s*\nAccount No\.\s*\nTotal Amount Payable\s*\n(\d{6,10})")

    period = re.search(r"Monthly Bill Summary for the period (\d{2}/\d{2}) to (\d{2}/\d{2})", text)

    bucket = _find(text, r"Total Charge for the Month\s*\.{3,}\s*([\d,.]+)", float)
    vat = _find(text, r"VAT \([\d,.]+%\)\.{3,}\s*([\d,.]+)", float)
    arrears = _find(text, r"Arrears\s*\.{3,}\s*([\d,.]+)", float)
    total_payable = _find(text, r"Total Payable\s*\.{3,}\s*([\d,.]+)", float)
    due_date = _find(text, r"Payment Due Date\s+(\d{2}/\d{2}/\d{4})")

    return {
        "bill_date": bill_date,
        "bill_no": bill_no,
        "account_no": account_no,
        "period_start_dm": period.group(1) if period else None,
        "period_end_dm": period.group(2) if period else None,
        "bucket": bucket,
        "vat": vat,
        "net": round(bucket - vat, 2) if bucket is not None and vat is not None else None,
        "arrears": arrears,
        "total_payable": total_payable,
        "due_date": due_date,
    }