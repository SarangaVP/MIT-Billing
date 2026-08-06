import uuid

from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile

from app.database import get_db
from app.schemas.mobitel_bill import MobitelBillPeriodOut, MobitelImportResult, MobitelStaticIpCostUpdateInput
from app.services import mobitel_bill_service

router = APIRouter(prefix="/mobitel/bills", tags=["mobitel-bills"])


@router.get("", response_model=list[MobitelBillPeriodOut])
def list_bill_periods(db: Session = Depends(get_db)):
    return mobitel_bill_service.list_bill_periods(db)


@router.post("/import", response_model=MobitelImportResult, status_code=201)
async def import_bill(
    label: str = Form(..., description='e.g. "June 2026"'),
    file: UploadFile = File(..., description="The Mobitel bill PDF"),
    portal_file: UploadFile | None = File(None, description="Optional: the 'Portal' sheet export (.xlsx) for per-SIM usage detail"),
    db: Session = Depends(get_db),
):
    with NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    portal_tmp_path = None
    if portal_file is not None:
        with NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            shutil.copyfileobj(portal_file.file, tmp)
            portal_tmp_path = tmp.name

    try:
        return mobitel_bill_service.import_mobitel_bill(db, tmp_path, label, portal_path=portal_tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)
        if portal_tmp_path:
            Path(portal_tmp_path).unlink(missing_ok=True)


@router.get("/{bill_period_id}/summary")
def get_bill_summary(bill_period_id: uuid.UUID, db: Session = Depends(get_db)):
    return mobitel_bill_service.get_summary(db, bill_period_id)


@router.put("/line-items/{line_item_id}/static-ip-cost")
def update_static_ip_cost(line_item_id: uuid.UUID, payload: MobitelStaticIpCostUpdateInput, db: Session = Depends(get_db)):
    """Sets this line item's static IP cost and recalculates the whole bill period's split."""
    return mobitel_bill_service.update_static_ip_cost(db, line_item_id, payload.cost)