"""
Primary extraction method for Dialog Data Bucket bills, same AI-first
policy as Mobitel: reads the PDF directly, resilient to Dialog changing
the bill's wording or layout. Falls back to dialog_data_pdf_parser.py
(regex) automatically if this raises or returns incomplete data — see
dialog_data_bill_service.import_dialog_data_bill for the fallback logic.
"""
import pathlib

from google import genai
from google.genai import types
from pydantic import BaseModel

MODEL_NAME = "gemini-3.1-flash-lite"

EXTRACTION_PROMPT = """\
Extract the following fields from this Dialog corporate data bucket bill \
PDF (a "TAX INVOICE" with a "Charges for Bill Period" section listing \
Data, Government Taxes & Levies, VAT, and a Total).

- invoice_date: the "InvoiceDate", formatted exactly as DD/MM/YYYY
- invoice_no: the "InvoiceNumber" (an alphanumeric code, e.g. \
"26JUL_BR03_110001805644")
- mobile_no: the "MOBILE NUMBER" this bill is for
- period_start: the bill period's start date, formatted exactly as \
DD/MM/YYYY
- period_end: the bill period's end date, formatted exactly as DD/MM/YYYY
- data_charge: the "Data" charge line, as a plain number with no \
currency symbol, no commas
- govt_taxes: the "Government Taxes & Levies" amount, as a plain number
- vat: the "VAT" amount from the Charges for Bill Period section (NOT \
the company's VAT registration number), as a plain number
- total: the "Total Charges for Bill Period" amount, as a plain number

If a field genuinely cannot be found, set it to null. Do not guess, \
estimate, or infer a value that isn't actually present."""


class DialogDataBillExtraction(BaseModel):
    invoice_date: str | None = None
    invoice_no: str | None = None
    mobile_no: str | None = None
    period_start: str | None = None
    period_end: str | None = None
    data_charge: float | None = None
    govt_taxes: float | None = None
    vat: float | None = None
    total: float | None = None


def extract_via_gemini(pdf_path: str, api_key: str) -> dict:
    """Raises on any failure — callers must catch and fall back to regex."""
    client = genai.Client(api_key=api_key)
    pdf_bytes = pathlib.Path(pdf_path).read_bytes()

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[
            types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
            EXTRACTION_PROMPT,
        ],
        config={
            "response_mime_type": "application/json",
            "response_schema": DialogDataBillExtraction,
        },
    )

    result = DialogDataBillExtraction.model_validate_json(response.text)

    net = (
        round(result.total - result.vat, 2)
        if result.total is not None and result.vat is not None
        else None
    )

    return {
        "invoice_date": result.invoice_date,
        "invoice_no": result.invoice_no,
        "mobile_no": result.mobile_no,
        "period_start": result.period_start,
        "period_end": result.period_end,
        "data_charge": result.data_charge,
        "govt_taxes": result.govt_taxes,
        "vat": result.vat,
        "total": result.total,
        "net": net,
    }