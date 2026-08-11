import uuid
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, Depends, Query, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.dialog_data_employee import (
    DialogDataEmployeeCreate, DialogDataEmployeeUpdate, DialogDataEmployeeOut, DialogDataConnectionCreate,
)
from app.services import dialog_data_employee_service
from app.services.dialog_data_sheet_sync import sync_dialog_data_sheet

router = APIRouter(prefix="/dialog-data/employees", tags=["dialog-data-employees"])


@router.get("", response_model=list[DialogDataEmployeeOut])
def list_employees(search: str | None = Query(None), db: Session = Depends(get_db)):
    return dialog_data_employee_service.list_employees(db, search=search)


@router.post("", response_model=DialogDataEmployeeOut, status_code=201)
def create_employee(payload: DialogDataEmployeeCreate, db: Session = Depends(get_db)):
    return dialog_data_employee_service.create_employee(db, payload)


@router.put("/{employee_id}", response_model=DialogDataEmployeeOut)
def update_employee(employee_id: uuid.UUID, payload: DialogDataEmployeeUpdate, db: Session = Depends(get_db)):
    return dialog_data_employee_service.update_employee(db, employee_id, payload)


@router.delete("/{employee_id}", response_model=DialogDataEmployeeOut)
def delete_employee(employee_id: uuid.UUID, db: Session = Depends(get_db)):
    return dialog_data_employee_service.soft_delete_employee(db, employee_id)


@router.post("/{employee_id}/connections", response_model=DialogDataEmployeeOut, status_code=201)
def add_connection(employee_id: uuid.UUID, payload: DialogDataConnectionCreate, db: Session = Depends(get_db)):
    return dialog_data_employee_service.add_connection(db, employee_id, payload)


@router.delete("/connections/{connection_id}", status_code=204)
def remove_connection(connection_id: uuid.UUID, db: Session = Depends(get_db)):
    dialog_data_employee_service.remove_connection(db, connection_id)


@router.post("/import")
async def import_employee_sheet(
    file: UploadFile = File(..., description="The Master sheet Excel export — treated as the full, current roster"),
    db: Session = Depends(get_db),
):
    with NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
    try:
        return sync_dialog_data_sheet(db, tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)