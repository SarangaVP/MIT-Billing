import uuid
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.dialog_data_bill import DialogDataBillPeriodOut, DialogDataImportResult
from app.services import dialog_data_bill_service

router = APIRouter(prefix="/dialog-data/bills", tags=["dialog-data-bills"])


@router.get("", response_model=list[DialogDataBillPeriodOut])
def list_bill_periods(db: Session = Depends(get_db)):
    return dialog_data_bill_service.list_bill_periods(db)


@router.post("/import", response_model=DialogDataImportResult, status_code=201)
async def import_bill(
    label: str = Form(..., description='e.g. "July 2026"'),
    file: UploadFile = File(..., description="The Dialog Data Bucket bill PDF"),
    bill_sheet_file: UploadFile | None = File(None, description="Optional: the 'Bill' sheet export (.xlsx) for per-connection usage detail"),
    db: Session = Depends(get_db),
):
    with NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    bill_sheet_tmp_path = None
    if bill_sheet_file is not None:
        with NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            shutil.copyfileobj(bill_sheet_file.file, tmp)
            bill_sheet_tmp_path = tmp.name

    try:
        return dialog_data_bill_service.import_dialog_data_bill(db, tmp_path, label, bill_sheet_path=bill_sheet_tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)
        if bill_sheet_tmp_path:
            Path(bill_sheet_tmp_path).unlink(missing_ok=True)


@router.get("/{bill_period_id}/summary")
def get_bill_summary(bill_period_id: uuid.UUID, db: Session = Depends(get_db)):
    return dialog_data_bill_service.get_summary(db, bill_period_id)


@router.delete("/{bill_period_id}", status_code=204)
def delete_bill_period(bill_period_id: uuid.UUID, db: Session = Depends(get_db)):
    dialog_data_bill_service.delete_bill_period(db, bill_period_id)