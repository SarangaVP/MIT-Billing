import uuid
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.slt_general_bill import (
    SltGeneralAccountOut, SltGeneralAccountUpdate, SltGeneralBillPeriodOut,
    SltGeneralBillLineItemOut, SltGeneralImportBatchResult,
)
from app.services import slt_general_bill_service

router = APIRouter(prefix="/slt/general", tags=["slt-general-bills"])


@router.get("/accounts", response_model=list[SltGeneralAccountOut])
def list_accounts(db: Session = Depends(get_db)):
    return slt_general_bill_service.list_accounts(db)


@router.put("/accounts/{account_id}", response_model=SltGeneralAccountOut)
def update_account_label(account_id: uuid.UUID, payload: SltGeneralAccountUpdate, db: Session = Depends(get_db)):
    return slt_general_bill_service.update_account_label(db, account_id, payload)


@router.get("/bills", response_model=list[SltGeneralBillPeriodOut])
def list_bill_periods(db: Session = Depends(get_db)):
    return slt_general_bill_service.list_bill_periods(db)


@router.post("/bills/import", response_model=SltGeneralImportBatchResult, status_code=201)
async def import_bills(
    label: str = Form(..., description='e.g. "June 2026"'),
    files: list[UploadFile] = File(..., description="Up to 4 general SLT account bill PDFs, uploaded together"),
    db: Session = Depends(get_db),
):
    results = []
    for file in files:
        with NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
        try:
            result = slt_general_bill_service.import_one_bill(db, tmp_path, file.filename or "unknown.pdf", label)
            results.append(result)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    return SltGeneralImportBatchResult(results=results)


@router.get("/bills/{bill_period_id}/line-items", response_model=list[SltGeneralBillLineItemOut])
def get_line_items(bill_period_id: uuid.UUID, db: Session = Depends(get_db)):
    return slt_general_bill_service.get_line_items(db, bill_period_id)


@router.delete("/bills/{bill_period_id}", status_code=204)
def delete_bill_period(bill_period_id: uuid.UUID, db: Session = Depends(get_db)):
    slt_general_bill_service.delete_bill_period(db, bill_period_id)