from sqlalchemy.orm import Session

from app.models.mobitel_static_ip_rate import MobitelStaticIpRate
from app.models.mobitel_employee import MobitelEmployee
from app.schemas.mobitel_static_ip_rate import MobitelStaticIpRateCreate


def list_static_ip_rates(db: Session) -> list[dict]:
    rows = (
        db.query(MobitelStaticIpRate, MobitelEmployee)
        .join(MobitelEmployee, MobitelEmployee.id == MobitelStaticIpRate.employee_id)
        .order_by(MobitelStaticIpRate.effective_from.desc())
        .all()
    )
    return [
        {
            "id": rate.id, "employee_id": rate.employee_id, "employee_name": employee.name,
            "cost": rate.cost, "effective_from": rate.effective_from, "created_at": rate.created_at,
        }
        for rate, employee in rows
    ]


def create_static_ip_rate(db: Session, payload: MobitelStaticIpRateCreate) -> MobitelStaticIpRate:
    rate = MobitelStaticIpRate(**payload.model_dump())
    db.add(rate)
    db.commit()
    db.refresh(rate)
    return rate


def get_active_static_ip_costs(db: Session, as_of) -> dict:
    rates = (
        db.query(MobitelStaticIpRate)
        .filter(MobitelStaticIpRate.effective_from <= as_of)
        .order_by(MobitelStaticIpRate.employee_id, MobitelStaticIpRate.effective_from.desc())
        .all()
    )
    result = {}
    for rate in rates:
        if rate.employee_id not in result:
            result[rate.employee_id] = rate.cost
    return result