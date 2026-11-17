"""Справочники, статистика по районам и базовое администрирование."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import ROLES, Category, District, Event, EventParticipant, Problem, User
from ..schemas import CategoryOut, DistrictOut, UserOut
from ..security import require_roles
from .auth import user_out

router = APIRouter(prefix="/api", tags=["Справочники и статистика"])


@router.get("/districts", response_model=list[DistrictOut])
def districts(db: Session = Depends(get_db)):
    return db.scalars(select(District).order_by(District.name)).all()


@router.get("/categories", response_model=list[CategoryOut])
def categories(db: Session = Depends(get_db)):
    return db.scalars(select(Category).order_by(Category.id)).all()


@router.get("/stats/districts")
def district_stats(db: Session = Depends(get_db)):
    """FR-06: показатели по каждому району Бишкека."""
    counts = db.execute(select(Problem.district_id, Problem.status, func.count()).group_by(Problem.district_id, Problem.status)).all()
    events = dict(db.execute(
        select(Problem.district_id, func.count(Event.id)).join(Event, Event.problem_id == Problem.id)
        .where(Event.status.in_(("planned", "fundraising", "funded"))).group_by(Problem.district_id)
    ).all())
    result = []
    for d in db.scalars(select(District).order_by(District.name)):
        by = {s: n for did, s, n in counts if did == d.id}
        result.append({
            "district_id": d.id, "name": d.name,
            "new": by.get("pending", 0),
            "on_check": by.get("extra_check", 0),
            "confirmed": by.get("confirmed", 0) + by.get("planned", 0),
            "in_progress": by.get("in_progress", 0),
            "resolved": by.get("resolved", 0),
            "events_planned": events.get(d.id, 0),
        })
    return result


@router.get("/stats/summary")
def summary(db: Session = Depends(get_db)):
    """FR-22 (базовая часть)."""
    by_status = dict(db.execute(select(Problem.status, func.count()).group_by(Problem.status)).all())
    by_cat = db.execute(select(Category.name, func.count(Problem.id)).join(Problem, isouter=True).group_by(Category.name)).all()
    return {
        "problems_total": sum(by_status.values()),
        "by_status": by_status,
        "by_category": [{"name": n, "count": c} for n, c in by_cat],
        "events_total": db.scalar(select(func.count()).select_from(Event)) or 0,
        "participants_total": db.scalar(select(func.count()).select_from(EventParticipant).where(EventParticipant.status != "cancelled")) or 0,
        "users_total": db.scalar(select(func.count()).select_from(User)) or 0,
    }


# ---- Администрирование (частично, FR-21) ----
class RoleIn(BaseModel):
    role: str
    district_ids: list[int] = []


@router.get("/admin/users", response_model=list[UserOut], tags=["Администрирование"])
def admin_users(db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))):
    return [user_out(u) for u in db.scalars(select(User).order_by(User.id)).all()]


@router.put("/admin/users/{uid}/role", response_model=UserOut, tags=["Администрирование"])
def set_role(uid: int, data: RoleIn, db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))):
    """Назначение ролей и закрепление модераторов за районами (FR-06)."""
    if data.role not in ROLES:
        raise HTTPException(400, "Неизвестная роль")
    u = db.get(User, uid)
    if not u:
        raise HTTPException(404, "Пользователь не найден")
    u.role = data.role
    u.districts = [db.get(District, d) for d in data.district_ids if db.get(District, d)] if data.role == "moderator" else []
    db.commit()
    return user_out(u)
