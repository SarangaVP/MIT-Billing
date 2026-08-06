from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.bucket_rate import BucketRateCreate, BucketRateOut
from app.services import bucket_rate_service

router = APIRouter(prefix="/bucket-rates", tags=["bucket-rates"])


@router.get("", response_model=list[BucketRateOut])
def list_bucket_rates(db: Session = Depends(get_db)):
    return bucket_rate_service.list_bucket_rates(db)


@router.post("", response_model=BucketRateOut, status_code=201)
def create_bucket_rate(payload: BucketRateCreate, db: Session = Depends(get_db)):
    return bucket_rate_service.create_bucket_rate(db, payload)