import shutil
import uuid
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.bill import ImportResult, BillSummaryRow, ApprovalOverrideInput, BillPeriodOut
from app.services import bill_service

router = APIRouter(prefix="/bills", tags=["bills"])

SUPPORTED_SUFFIXES = {".pdf": "pdf", ".xls": "xls"}


@router.get("", response_model=list[BillPeriodOut])
def list_bill_periods(db: Session = Depends(get_db)):
    return bill_service.list_bill_periods(db)


@router.get("/{bill_period_id}", response_model=BillPeriodOut)
def get_bill_period(bill_period_id: uuid.UUID, db: Session = Depends(get_db)):
    return bill_service.get_bill_period(db, bill_period_id)


@router.post("/import", response_model=ImportResult, status_code=201)
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
        return bill_service.import_bill_file(db, tmp_path, label, source_format)
    finally:
        Path(tmp_path).unlink(missing_ok=True)


@router.get("/{bill_period_id}/summary", response_model=list[BillSummaryRow])
def get_bill_summary(bill_period_id: uuid.UUID, db: Session = Depends(get_db)):
    return bill_service.get_summary(db, bill_period_id)


@router.delete("/{bill_period_id}", status_code=204)
def delete_bill_period(bill_period_id: uuid.UUID, db: Session = Depends(get_db)):
    bill_service.delete_bill_period(db, bill_period_id)


@router.put("/line-items/{line_item_id}/approval-override", response_model=BillSummaryRow)
def set_approval_override(line_item_id: uuid.UUID, payload: ApprovalOverrideInput, db: Session = Depends(get_db)):
    return bill_service.set_approval_override(db, line_item_id, payload)