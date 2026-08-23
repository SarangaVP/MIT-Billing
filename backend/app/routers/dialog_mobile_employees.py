import uuid
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, Depends, Query, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.dialog_mobile_employee import DialogMobileEmployeeCreate, DialogMobileEmployeeUpdate, DialogMobileEmployeeOut
from app.schemas.dialog_mobile_mobile_number import DialogMobileMobileNumberCreate, DialogMobileMobileNumberOut, DialogMobileMobileNumberUpdate
from app.services import dialog_mobile_employee_service
from app.services.dialog_mobile_sheet_sync import sync_employee_sheet

router = APIRouter(prefix="/dialog-mobile/employees", tags=["dialog-mobile-employees"])


@router.get("", response_model=list[DialogMobileEmployeeOut])
def list_employees(
    search: str | None = Query(None, description="Matches name, EMP No, or any of the employee's mobile numbers"),
    lob: str | None = None,
    include_deleted: bool = False,
    db: Session = Depends(get_db),
):
    return dialog_mobile_employee_service.list_employees(db, search=search, lob=lob, include_deleted=include_deleted)


@router.post("", response_model=DialogMobileEmployeeOut, status_code=201)
def create_employee(payload: DialogMobileEmployeeCreate, db: Session = Depends(get_db)):
    return dialog_mobile_employee_service.create_employee(db, payload)


@router.get("/{employee_id}", response_model=DialogMobileEmployeeOut)
def get_employee(employee_id: uuid.UUID, db: Session = Depends(get_db)):
    return dialog_mobile_employee_service.get_employee(db, employee_id)


@router.put("/{employee_id}", response_model=DialogMobileEmployeeOut)
def update_employee(employee_id: uuid.UUID, payload: DialogMobileEmployeeUpdate, db: Session = Depends(get_db)):
    return dialog_mobile_employee_service.update_employee(db, employee_id, payload)


@router.delete("/{employee_id}", response_model=DialogMobileEmployeeOut)
def delete_employee(employee_id: uuid.UUID, db: Session = Depends(get_db)):
    """Soft delete — flags the record, never removes billing history."""
    return dialog_mobile_employee_service.soft_delete_employee(db, employee_id)


@router.post("/{employee_id}/mobile-numbers", response_model=DialogMobileMobileNumberOut, status_code=201)
def add_mobile_number(employee_id: uuid.UUID, payload: DialogMobileMobileNumberCreate, db: Session = Depends(get_db)):
    return dialog_mobile_employee_service.add_mobile_number(db, employee_id, payload)


@router.delete("/{employee_id}/mobile-numbers/{number_id}", response_model=DialogMobileMobileNumberOut)
def remove_mobile_number(employee_id: uuid.UUID, number_id: uuid.UUID, db: Session = Depends(get_db)):
    """Marks the number inactive — does not delete the row (keeps billing history intact)."""
    return dialog_mobile_employee_service.remove_mobile_number(db, employee_id, number_id)


@router.put("/mobile-numbers/{number_id}/project-label", response_model=DialogMobileMobileNumberOut)
def update_mobile_number_project_label(number_id: uuid.UUID, payload: DialogMobileMobileNumberUpdate, db: Session = Depends(get_db)):
    return dialog_mobile_employee_service.update_mobile_number_project_label(db, number_id, payload.project_label)


@router.post("/import")
async def import_employee_sheet(
    file: UploadFile = File(..., description="The Master sheet Excel export — treated as the full, current roster"),
    db: Session = Depends(get_db),
):
    """
    Syncs the roster from an uploaded sheet — see dialog_mobile_sheet_sync.py
    for exactly what this does (update in place, retire what's missing,
    never delete). Same logic the CLI script uses, so both paths always
    behave identically.
    """
    with NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
    try:
        return sync_employee_sheet(db, tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)