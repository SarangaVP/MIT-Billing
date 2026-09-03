import uuid
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, Depends, Query, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.mobitel_employee import (
    MobitelEmployeeCreate, MobitelEmployeeUpdate, MobitelEmployeeOut, MobitelConnectionCreate,
    MobitelConnectionOut, MobitelConnectionDefaultStaticIpInput,
)
from app.services import mobitel_employee_service
from app.services.mobitel_sheet_sync import sync_mobitel_sheet

router = APIRouter(prefix="/mobitel/employees", tags=["mobitel-employees"])


@router.get("", response_model=list[MobitelEmployeeOut])
def list_employees(search: str | None = Query(None), db: Session = Depends(get_db)):
    return mobitel_employee_service.list_employees(db, search=search)


@router.post("", response_model=MobitelEmployeeOut, status_code=201)
def create_employee(payload: MobitelEmployeeCreate, db: Session = Depends(get_db)):
    return mobitel_employee_service.create_employee(db, payload)


@router.put("/{employee_id}", response_model=MobitelEmployeeOut)
def update_employee(employee_id: uuid.UUID, payload: MobitelEmployeeUpdate, db: Session = Depends(get_db)):
    return mobitel_employee_service.update_employee(db, employee_id, payload)


@router.delete("/{employee_id}", response_model=MobitelEmployeeOut)
def delete_employee(employee_id: uuid.UUID, db: Session = Depends(get_db)):
    return mobitel_employee_service.soft_delete_employee(db, employee_id)


@router.post("/{employee_id}/connections", response_model=MobitelEmployeeOut, status_code=201)
def add_connection(employee_id: uuid.UUID, payload: MobitelConnectionCreate, db: Session = Depends(get_db)):
    return mobitel_employee_service.add_connection(db, employee_id, payload)


@router.delete("/connections/{connection_id}", status_code=204)
def remove_connection(connection_id: uuid.UUID, db: Session = Depends(get_db)):
    mobitel_employee_service.remove_connection(db, connection_id)


@router.put("/connections/{connection_id}/default-static-ip-cost", response_model=MobitelConnectionOut)
def set_default_static_ip_cost(connection_id: uuid.UUID, payload: MobitelConnectionDefaultStaticIpInput, db: Session = Depends(get_db)):
    """
    Sets a persistent static IP cost applied automatically on every
    future bill import for this connection (e.g. 711434957 always
    carries Rs. 1500) — doesn't touch already-imported bill periods.
    """
    return mobitel_employee_service.set_default_static_ip_cost(db, connection_id, payload.default_static_ip_cost)


@router.post("/import")
async def import_employee_sheet(
    file: UploadFile = File(..., description="The Summary sheet Excel export — treated as the full, current roster"),
    db: Session = Depends(get_db),
):
    with NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
    try:
        return sync_mobitel_sheet(db, tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)