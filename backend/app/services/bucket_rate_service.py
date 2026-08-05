from sqlalchemy.orm import Session

from app.models.bucket_rate import BucketRate
from app.schemas.bucket_rate import BucketRateCreate


def list_bucket_rates(db: Session) -> list[BucketRate]:
    return db.query(BucketRate).order_by(BucketRate.effective_from.desc()).all()


def create_bucket_rate(db: Session, payload: BucketRateCreate) -> BucketRate:
    rate = BucketRate(**payload.model_dump())
    db.add(rate)
    db.commit()
    db.refresh(rate)
    return rate