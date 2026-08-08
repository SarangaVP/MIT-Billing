"""
Parses a single-page SLT Mobitel corporate bill PDF. Unlike Dialog, this
bill has NO per-employee breakdown at all — just company-wide totals.

The PDF's header block (Bill No, Account No, company address) gets badly
scrambled by PDF-to-text extraction — labels and values end up interleaved
in an order that doesn't match the visual layout. The "Account Summary"
section further down extracts cleanly line-by-line, so that's what the
actual financial figures (Bucket, VAT, Arrears, Total Payable) are parsed
from. Header metadata (Bill No, Account No) is extracted best-effort from
the known, fixed structure of Millennium ITESP's own bills specifically —
if that ever breaks, it only affects metadata, not the money.

CRITICAL: filler dots in "Total Charge for the Month ....... 330,646.98"
must be matched with \\.{3,} (3+ consecutive dots), not \\.+ (one or more) —
some labels contain their own decimal point (e.g. "Cess (2%) (Eff 2.04%)")
which \\.+ would incorrectly latch onto instead of the real filler run.

CONFIRMED REAL FORMAT CHANGE (June'26 -> July'26 bill): the bucket-total
line's label changed from "Total Charge for the Month" to "Total Charges
for Bill Period", and Bill No changed from a pure numeric string
("262145722") to an alphanumeric one ("26JUL_MBPPT_264227932"). Both
label variants are matched below — this is exactly the scenario the
AI-first extraction (gemini_pdf_extractor.py) exists for, but the regex
fallback needs to keep working too when no API key is configured or the
AI call fails.
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
    bill_no = _find(
        text,
        r"Bill Date\s+\d{2}/\d{2}/\d{4}\s*\nAccount No\.\s*\nTotal Amount Payable\s*\n([\w]{6,30})",
    )

    period = re.search(r"Monthly Bill Summary for the period (\d{2}/\d{2}) to (\d{2}/\d{2})", text)

    # Two known label variants for the same figure — try both.
    bucket = _find(text, r"Total Charge for the Month\s*\.{3,}\s*([\d,.]+)", float)
    if bucket is None:
        bucket = _find(text, r"Total Charges for Bill Period\s*\.{3,}\s*([\d,.]+)", float)

    vat = _find(text, r"VAT \([\d,.]+%\)\.{3,}\s*([\d,.]+)", float)
    arrears = _find(text, r"Arrears\s*\.{3,}\s*([\d,.]+)", float)
    total_payable = _find(text, r"Total Payable\s*\.{3,}\s*([\d,.]+)", float)
    due_date = _find(text, r"Payment Due Date\s+(\d{2}/\d{2}/\d{4})")

    return {
        "bill_date": bill_date,
        "bill_no": bill_no,
        "account_no": account_no,
        "period_start_dm": period.group(1) if period else None,   # "DD/MM", no year
        "period_end_dm": period.group(2) if period else None,
        "bucket": bucket,
        "vat": vat,
        "net": round(bucket - vat, 2) if bucket is not None and vat is not None else None,
        "arrears": arrears,
        "total_payable": total_payable,
        "due_date": due_date,
    }