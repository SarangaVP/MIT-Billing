from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.mobitel_static_ip_rate import MobitelStaticIpRateCreate, MobitelStaticIpRateOut
from app.services import mobitel_static_ip_service

router = APIRouter(prefix="/mobitel/static-ip-rates", tags=["mobitel-static-ip-rates"])


@router.get("", response_model=list[MobitelStaticIpRateOut])
def list_static_ip_rates(db: Session = Depends(get_db)):
    return mobitel_static_ip_service.list_static_ip_rates(db)


@router.post("", response_model=MobitelStaticIpRateOut, status_code=201)
def create_static_ip_rate(payload: MobitelStaticIpRateCreate, db: Session = Depends(get_db)):
    return mobitel_static_ip_service.create_static_ip_rate(db, payload)