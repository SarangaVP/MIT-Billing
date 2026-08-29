import shutil
import uuid
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.dialog_mobile_bill import (
    DialogMobileImportResult, DialogMobileBillSummaryRow, DialogMobileApprovalOverrideInput,
    DialogMobileBucketExclusionInput, DialogMobileBucketRateOverrideInput, DialogMobileLineItemChargeUpdateInput,
    DialogMobileBillPeriodOut, DialogMobileDataBucketSelectionInput, DialogMobileSalaryDeductionOverrideInput,
)
from app.services import dialog_mobile_bill_service

router = APIRouter(prefix="/dialog-mobile/bills", tags=["dialog-mobile-bills"])

SUPPORTED_SUFFIXES = {".pdf": "pdf", ".xls": "xls"}


@router.get("", response_model=list[DialogMobileBillPeriodOut])
def list_bill_periods(db: Session = Depends(get_db)):
    return dialog_mobile_bill_service.list_bill_periods(db)


@router.get("/{bill_period_id}", response_model=DialogMobileBillPeriodOut)
def get_bill_period(bill_period_id: uuid.UUID, db: Session = Depends(get_db)):
    return dialog_mobile_bill_service.get_bill_period(db, bill_period_id)


@router.post("/import", response_model=DialogMobileImportResult, status_code=201)
async def import_bill(
    label: str = Form(..., description='e.g. "July 2026"'),
    file: UploadFile = File(..., description="The bill file — .pdf or .xls"),
    db: Session = Depends(get_db),
):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}' — expected .pdf or .xls",
        )
    source_format = SUPPORTED_SUFFIXES[suffix]

    with NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        return dialog_mobile_bill_service.import_bill_file(db, tmp_path, label, source_format)
    finally:
        Path(tmp_path).unlink(missing_ok=True)


@router.get("/{bill_period_id}/summary", response_model=list[DialogMobileBillSummaryRow])
def get_bill_summary(bill_period_id: uuid.UUID, db: Session = Depends(get_db)):
    return dialog_mobile_bill_service.get_summary(db, bill_period_id)


@router.delete("/{bill_period_id}", status_code=204)
def delete_bill_period(bill_period_id: uuid.UUID, db: Session = Depends(get_db)):
    dialog_mobile_bill_service.delete_bill_period(db, bill_period_id)


@router.put("/line-items/{line_item_id}/approval-override", response_model=DialogMobileBillSummaryRow)
def set_approval_override(line_item_id: uuid.UUID, payload: DialogMobileApprovalOverrideInput, db: Session = Depends(get_db)):
    return dialog_mobile_bill_service.set_approval_override(db, line_item_id, payload)


@router.put("/line-items/{line_item_id}/salary-deduction-override", response_model=DialogMobileBillSummaryRow)
def set_salary_deduction_override(line_item_id: uuid.UUID, payload: DialogMobileSalaryDeductionOverrideInput, db: Session = Depends(get_db)):
    """
    Sets (or clears, if null) an exact manual Salary Deduction figure for
    this line item, overriding the computed value entirely.
    """
    return dialog_mobile_bill_service.set_salary_deduction_override(db, line_item_id, payload.salary_deduction_override)


@router.put("/{bill_period_id}/bucket-rate-override", response_model=list[DialogMobileBillSummaryRow])
def set_bucket_rate_override(bill_period_id: uuid.UUID, payload: DialogMobileBucketRateOverrideInput, db: Session = Depends(get_db)):
    """
    Sets (or clears, if both fields are null) a bucket rate that applies
    ONLY to this bill period — unlike the standard rate table, which
    applies from its effective date forward to every later month too.
    """
    return dialog_mobile_bill_service.set_bucket_rate_override(db, bill_period_id, payload.bucket_cost_override, payload.bucket_vat_override)


@router.put("/line-items/{line_item_id}/bucket-exclusion", response_model=DialogMobileBillSummaryRow)
def set_bucket_exclusion(line_item_id: uuid.UUID, payload: DialogMobileBucketExclusionInput, db: Session = Depends(get_db)):
    return dialog_mobile_bill_service.set_bucket_exclusion(db, line_item_id, payload.is_bucket_excluded)


@router.put("/{bill_period_id}/data-bucket-number", response_model=list[DialogMobileBillSummaryRow])
def set_data_bucket_number(bill_period_id: uuid.UUID, payload: DialogMobileDataBucketSelectionInput, db: Session = Depends(get_db)):
    """
    Selects (or clears, if data_bucket_mobile_no is null) the connection
    whose own charges become the automatically-split bucket pool for this
    bill period — replaces manually typing a rate via bucket-rate-override.
    """
    return dialog_mobile_bill_service.set_data_bucket_number(db, bill_period_id, payload.data_bucket_mobile_no)


@router.put("/line-items/{line_item_id}/charges", response_model=DialogMobileBillSummaryRow)
def update_line_item_charges(line_item_id: uuid.UUID, payload: DialogMobileLineItemChargeUpdateInput, db: Session = Depends(get_db)):
    """
    Manual correction to a line item's raw charge figures for this bill
    period ("Manage data bucket" in the UI) — net_amount/total recompute
    automatically from these on the next read.
    """
    return dialog_mobile_bill_service.update_line_item_charges(db, line_item_id, payload)