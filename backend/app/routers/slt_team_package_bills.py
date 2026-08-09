import uuid
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.slt_bill import SltTeamPackageBillPeriodOut, SltTeamPackageImportResult, SltTeamPackageBillLineItemOut
from app.services import slt_team_package_bill_service

router = APIRouter(prefix="/slt/team-package/bills", tags=["slt-team-package-bills"])


@router.get("", response_model=list[SltTeamPackageBillPeriodOut])
def list_bill_periods(db: Session = Depends(get_db)):
    return slt_team_package_bill_service.list_bill_periods(db)


@router.post("/import", response_model=SltTeamPackageImportResult, status_code=201)
async def import_bill(
    label: str = Form(..., description='e.g. "June 2026"'),
    file: UploadFile = File(..., description="The SLT team package (004 767 150X) bill PDF"),
    excel_file: UploadFile = File(..., description="The Summary Excel for this month — REQUIRED, uploaded fresh every time"),
    db: Session = Depends(get_db),
):
    with NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp)
        pdf_tmp_path = tmp.name

    with NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        shutil.copyfileobj(excel_file.file, tmp)
        excel_tmp_path = tmp.name

    try:
        return slt_team_package_bill_service.import_team_package_bill(db, pdf_tmp_path, excel_tmp_path, label)
    finally:
        Path(pdf_tmp_path).unlink(missing_ok=True)
        Path(excel_tmp_path).unlink(missing_ok=True)


@router.get("/{bill_period_id}/summary", response_model=list[SltTeamPackageBillLineItemOut])
def get_bill_summary(bill_period_id: uuid.UUID, db: Session = Depends(get_db)):
    return slt_team_package_bill_service.get_summary(db, bill_period_id)


@router.delete("/{bill_period_id}", status_code=204)
def delete_bill_period(bill_period_id: uuid.UUID, db: Session = Depends(get_db)):
    slt_team_package_bill_service.delete_bill_period(db, bill_period_id)