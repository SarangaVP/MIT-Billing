import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.dialog_mobile_mobile_number import DialogMobileMobileNumberStatus


class DialogMobileMobileNumberOut(BaseModel):
    id: uuid.UUID
    mobile_no: str
    is_primary: bool
    status: DialogMobileMobileNumberStatus
    project_label: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DialogMobileMobileNumberCreate(BaseModel):
    mobile_no: str
    is_primary: bool = False
    project_label: str | None = None


class DialogMobileMobileNumberUpdate(BaseModel):
    project_label: str | None = None