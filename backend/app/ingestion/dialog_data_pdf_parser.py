"""
Regex-based fallback parser for Dialog Data Bucket bills. Primary
extraction is Gemini (see gemini_dialog_data_extractor.py) — this only
runs if that fails or returns incomplete data.

This PDF is much cleaner than Mobitel's: full DD/MM/YYYY dates (no
DD/MM-only ambiguity), and no embedded decimal points inside labels to
collide with the amount patterns.
"""
import re

import pypdf


def _find(text: str, pattern: str, cast=str):
    m = re.search(pattern, text)
    if not m:
        return None
    val = m.group(1).replace(",", "")
    return cast(val)


def parse_dialog_data_bill(pdf_path: str) -> dict:
    reader = pypdf.PdfReader(pdf_path)
    text = reader.pages[0].extract_text() or ""

    invoice_date = _find(text, r"InvoiceDate:(\d{2}/\d{2}/\d{4})")
    invoice_no = _find(text, r"InvoiceNumber:([\w_]+)")
    mobile_no = _find(text, r"InvoiceNumber:[\w_]+\s*\n(\d{9,10})\n")
    period = re.search(r"(\d{2}/\d{2}/\d{4})\s*-(\d{2}/\d{2}/\d{4})", text)

    data_charge = _find(text, r"Data\s+([\d,]+\.\d{2})", float)
    govt_taxes = _find(text, r"Government Taxes & Levies\s+([\d,]+\.\d{2})", float)
    vat = _find(text, r"VAT\s+([\d,]+\.\d{2})", float)
    total = _find(text, r"Total Charges for Bill Period\s+([\d,]+\.\d{2})", float)

    return {
        "invoice_date": invoice_date,
        "invoice_no": invoice_no,
        "mobile_no": mobile_no,
        "period_start": period.group(1) if period else None,   # full DD/MM/YYYY, unlike Mobitel
        "period_end": period.group(2) if period else None,
        "data_charge": data_charge,
        "govt_taxes": govt_taxes,
        "vat": vat,
        "total": total,
        "net": round(total - vat, 2) if total is not None and vat is not None else None,
    }