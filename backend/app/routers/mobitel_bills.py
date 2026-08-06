import uuid
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.mobitel_bill import MobitelBillPeriodOut, MobitelImportResult
from app.services import mobitel_bill_service

router = APIRouter(prefix="/mobitel/bills", tags=["mobitel-bills"])


@router.get("", response_model=list[MobitelBillPeriodOut])
def list_bill_periods(db: Session = Depends(get_db)):
    return mobitel_bill_service.list_bill_periods(db)


@router.post("/import", response_model=MobitelImportResult, status_code=201)
async def import_bill(
    label: str = Form(..., description='e.g. "June 2026"'),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    with NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
    try:
        return mobitel_bill_service.import_mobitel_bill(db, tmp_path, label)
    finally:
        Path(tmp_path).unlink(missing_ok=True)


@router.get("/{bill_period_id}/summary")
def get_bill_summary(bill_period_id: uuid.UUID, db: Session = Depends(get_db)):
    return mobitel_bill_service.get_summary(db, bill_period_id)