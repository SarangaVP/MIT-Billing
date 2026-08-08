"""
Extraction for the SLT team package bill (account 004 767 150X). GEMINI
ONLY, per explicit instruction — no regex fallback for this module. If
Gemini fails (missing/invalid API key, network error, malformed
response), the import fails outright with a clear error rather than
silently falling back to a weaker method or guessing.

Doesn't need per-employee line items from the PDF — those come entirely
from that month's uploaded Summary Excel, parsed separately. Only needs
the bill's own header/total figures.
"""
import pathlib

from google import genai
from google.genai import types
from pydantic import BaseModel

MODEL_NAME = "gemini-3.1-flash-lite"

EXTRACTION_PROMPT = """\
Extract the following fields from this SLT Mobitel Tax Invoice PDF (an \
Enterprise account bill with a "Summary of Invoice" box and a "Details \
of Charges for the Period" section).

- account_no: the "Account Number" (may contain letters, e.g. "004 767 150X")
- invoice_no: the "Invoice Number"
- billing_date: the "Billing Date", formatted exactly as DD/MM/YYYY
- period_start: the start of the "Billing Period", formatted exactly as DD/MM/YYYY
- period_end: the end of the "Billing Period", formatted exactly as DD/MM/YYYY
- due_date: the "Payment due date", formatted exactly as DD/MM/YYYY
- balance_bf: the "Balance B/F" amount, as a plain number with no currency symbol, no commas
- payments_received: the "Payments received" amount, as a plain number
- cess: the "CESS" amount under Taxes & Levies, as a plain number
- sscl: the "Recovery in lieu of SSCL" amount, as a plain number
- vat: the VAT amount (e.g. "VAT-18%"), as a plain number
- charges_for_period: the "Total Charges for the Period" amount, as a plain number
- total_payable: the "Total payable" amount from the Summary of Invoice box, as a plain number

If a field genuinely cannot be found, set it to null. Do not guess, \
estimate, or infer a value that isn't actually present."""


class SltTeamPackageExtraction(BaseModel):
    account_no: str | None = None
    invoice_no: str | None = None
    billing_date: str | None = None
    period_start: str | None = None
    period_end: str | None = None
    due_date: str | None = None
    balance_bf: float | None = None
    payments_received: float | None = None
    cess: float | None = None
    sscl: float | None = None
    vat: float | None = None
    charges_for_period: float | None = None
    total_payable: float | None = None


def extract_via_gemini(pdf_path: str, api_key: str) -> dict:
    """Raises on any failure — this module has no fallback, so a raised
    exception here should surface directly as a failed import."""
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
            "response_schema": SltTeamPackageExtraction,
        },
    )

    result = SltTeamPackageExtraction.model_validate_json(response.text)
    return result.model_dump()