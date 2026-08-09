"""
Extraction for the 4 SLT "general" account bills. GEMINI ONLY, per
explicit instruction — no regex fallback. Unlike the team package bill,
these have NO persistent employee roster to fall back on for detail —
the itemized charges must come directly from the PDF, since real
examples show wildly different shapes per account (broadband, static
IP, fiber, voice VAS, PeoTV, business internet).
"""
import pathlib

from google import genai
from google.genai import types
from pydantic import BaseModel

MODEL_NAME = "gemini-3.1-flash-lite"

EXTRACTION_PROMPT = """\
Extract the following fields from this SLT Mobitel Tax Invoice PDF (an \
Enterprise account bill with a "Summary of Invoice" box and a "Details \
of Charges for the Period" section). The PDF may span multiple pages —
read all pages; the itemized charges and final Taxes & Levies totals \
may appear on a later page than the summary box.

- account_no: the "Account Number" (may contain letters, e.g. "001 614 8516")
- invoice_no: the "Invoice Number"
- billing_date: the "Billing Date", formatted exactly as DD/MM/YYYY
- period_start: the start of the "Billing Period", formatted exactly as DD/MM/YYYY
- period_end: the end of the "Billing Period", formatted exactly as DD/MM/YYYY
- due_date: the "Payment due date", formatted exactly as DD/MM/YYYY
- balance_bf: the "Balance B/F" amount, as a plain number with no currency symbol, no commas
- payments_received: the "Payments received" amount, as a plain number
- charges_for_period: the "Total Charges for the Period" amount, as a plain number
- total_payable: the "Total payable" amount from the Summary of Invoice box, as a plain number
- line_items: a list of every individual charge line under "Details of Charges for the Period", \
INCLUDING the Taxes & Levies lines (e.g. "CESS", "Recovery in lieu of SSCL", "VAT-18%", \
"Telecommunication Levy-15%" if present). Each item has:
  - description: the charge's description exactly as printed (e.g. "SLT BroadBand Service Any Xtreme [Rental]")
  - amount: the amount as a plain number, no currency symbol, no commas
  Do NOT include lines that show no amount (e.g. a sub-heading like a phone number or account \
code with nothing billed on that line, or a "Free" charge with no numeric value).

If a field genuinely cannot be found, set it to null. Do not guess, \
estimate, or infer a value that isn't actually present."""


class SltGeneralLineItem(BaseModel):
    description: str
    amount: float


class SltGeneralBillExtraction(BaseModel):
    account_no: str | None = None
    invoice_no: str | None = None
    billing_date: str | None = None
    period_start: str | None = None
    period_end: str | None = None
    due_date: str | None = None
    balance_bf: float | None = None
    payments_received: float | None = None
    charges_for_period: float | None = None
    total_payable: float | None = None
    line_items: list[SltGeneralLineItem] = []


def extract_via_gemini(pdf_path: str, api_key: str) -> dict:
    """Raises on any failure — this module has no fallback."""
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
            "response_schema": SltGeneralBillExtraction,
        },
    )

    result = SltGeneralBillExtraction.model_validate_json(response.text)
    return result.model_dump()