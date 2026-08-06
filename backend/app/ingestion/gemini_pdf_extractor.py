"""
Primary extraction method for Mobitel bills. Uses Gemini 3.1 Flash-Lite to
read the PDF directly (no text-extraction step, no regex) — resilient to
Mobitel changing their bill's wording or layout, unlike the regex parser.

Falls back to the regex parser (mobitel_pdf_parser.py) automatically if
this raises for ANY reason: missing/invalid API key, network error, rate
limit, malformed response, or the model itself returning incomplete data.
See mobitel_bill_service.import_mobitel_bill for the actual fallback logic
— this module only extracts; it never decides whether to fall back.
"""
import pathlib

from google import genai
from google.genai import types
from pydantic import BaseModel

MODEL_NAME = "gemini-3.1-flash-lite"

EXTRACTION_PROMPT = """\
Extract the following fields from this Mobitel/SLT corporate mobile data \
bucket bill PDF. This is a single-page invoice with a company header, an \
"Account Summary" section with a monthly bill breakdown, and payment terms.

- bill_date: the "Bill Date", formatted exactly as DD/MM/YYYY
- bill_no: the "Bill No." / Bill Number
- account_no: the "Account No." / Account Number
- period_start_dm: the billing period's start date, formatted DD/MM only \
(no year) — e.g. from a line like "Monthly Bill Summary for the period \
25/05 to 24/06", this would be "25/05"
- period_end_dm: the billing period's end date, formatted DD/MM only (no \
year) — from the same line, this would be "24/06"
- bucket: the "Total Charge for the Month" amount, as a plain number with \
no currency symbol, no commas, no thousands separators
- vat: the VAT amount from the Account Summary section, as a plain number
- arrears: the "Arrears" / "Balance as at last bill" amount, as a plain \
number
- total_payable: the "Total Payable" / "Total Amount Payable" amount, as \
a plain number
- due_date: the "Payment Due Date", formatted exactly as DD/MM/YYYY

If a field genuinely cannot be found in the document, set it to null. Do \
not guess, estimate, or infer a value that isn't actually present."""


class MobitelBillExtraction(BaseModel):
    bill_date: str | None = None
    bill_no: str | None = None
    account_no: str | None = None
    period_start_dm: str | None = None
    period_end_dm: str | None = None
    bucket: float | None = None
    vat: float | None = None
    arrears: float | None = None
    total_payable: float | None = None
    due_date: str | None = None


def extract_via_gemini(pdf_path: str, api_key: str) -> dict:
    """
    Raises on any failure (network, auth, malformed response) — callers
    must catch and fall back to the regex parser. Never silently returns
    partial/guessed data.
    """
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
            "response_schema": MobitelBillExtraction,
        },
    )

    result = MobitelBillExtraction.model_validate_json(response.text)

    return {
        "bill_date": result.bill_date,
        "bill_no": result.bill_no,
        "account_no": result.account_no,
        "period_start_dm": result.period_start_dm,
        "period_end_dm": result.period_end_dm,
        "bucket": result.bucket,
        "vat": result.vat,
        "arrears": result.arrears,
        "total_payable": result.total_payable,
        "due_date": result.due_date,
    }