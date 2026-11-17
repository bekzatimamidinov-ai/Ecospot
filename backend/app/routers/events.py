from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import AuditLog, Event, EventParticipant, Problem, User
from ..notify import notify
from ..schemas import EventIn, EventOut, EventStatusIn, ParticipantOut
from ..security import get_current_user, get_current_user_optional, require_roles

router = APIRouter(prefix="/api/events", tags=["Мероприятия"])

# Связь статуса мероприятия со статусом проблемы (UC-03: «Система обновляет статус проблемы»)
PROBLEM_STATUS_BY_EVENT = {"planned": "planned", "in_progress": "in_progress", "completed": "resolved"}
EVENT_TRANSITIONS = {
    "draft": {"planned", "cancelled"},
    "planned": {"in_progress", "cancelled"},
    "in_progress": {"awaiting_review", "completed", "cancelled"},
    "awaiting_review": {"completed", "in_progress"},
}


def active_count(db: Session, eid: int) -> int:
    return db.scalar(select(func.count()).select_from(EventParticipant).where(
        EventParticipant.event_id == eid, EventParticipant.status != "cancelled")) or 0


def to_out(db: Session, e: Event, user: User | None) -> EventOut:
    out = EventOut.model_validate(e)
    out.problem_title = e.problem.title
    out.participants_count = active_count(db, e.id)
    if user:
        out.registered_by_me = db.scalar(select(EventParticipant).where(
            EventParticipant.event_id == e.id, EventParticipant.user_id == user.id,
            EventParticipant.status != "cancelled")) is not None
    return out


def get_event(db: Session, eid: int) -> Event:
    e = db.get(Event, eid)
    if not e:
        raise HTTPException(404, "Мероприятие не найдено")
    return e


def participant_ids(e: Event) -> list[int]:
    return [p.user_id for p in e.participants if p.status != "cancelled"]


@router.get("", response_model=list[EventOut])
def list_events(db: Session = Depends(get_db), user: User | None = Depends(get_current_user_optional),
                type: str | None = None, status: list[str] | None = Query(None),
                district_id: int | None = None, upcoming: bool = False, mine: bool = False):
    stmt = select(Event).join(Problem)
    if type:
        stmt = stmt.where(Event.type == type)
    if status:
        stmt = stmt.where(Event.status.in_(status))
    else:
        stmt = stmt.where(Event.status != "draft")
    if district_id:
        stmt = stmt.where(Problem.district_id == district_id)
    if upcoming:
        stmt = stmt.where(Event.starts_at >= datetime.now(timezone.utc), Event.status.in_(("planned", "fundraising", "funded")))
    if mine and user:
        stmt = stmt.where(Event.organizer_id == user.id)
    return [to_out(db, e, user) for e in db.scalars(stmt.order_by(Event.starts_at)).all()]


@router.get("/participating", response_model=list[EventOut])
def participating(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(Event).join(EventParticipant).where(
        EventParticipant.user_id == user.id, EventParticipant.status != "cancelled")).all()
    return [to_out(db, e, user) for e in rows]


@router.post("", response_model=EventOut, status_code=201)
def create_event(data: EventIn, db: Session = Depends(get_db),
                 user: User = Depends(require_roles("organizer", "admin"))):
    p = db.get(Problem, data.problem_id)
    if not p or p.status not in ("confirmed", "planned", "in_progress"):
        raise HTTPException(400, "Мероприятие можно создать только для подтверждённой проблемы")
    if data.type == "funded":
        raise HTTPException(501, "Финансируемые мероприятия будут доступны на следующем этапе")
    e = Event(**data.model_dump(exclude={"lat", "lng"}), lat=data.lat or p.lat, lng=data.lng or p.lng,
              organizer_id=user.id, status="planned")
    db.add(e)
    db.flush()
    if p.status == "confirmed":
        p.status = "planned"
    db.add(AuditLog(user_id=user.id, action="create", entity="event", entity_id=e.id))
    db.commit()
    db.refresh(e)
    return to_out(db, e, user)


@router.get("/{eid}", response_model=EventOut)
def event_detail(eid: int, db: Session = Depends(get_db), user: User | None = Depends(get_current_user_optional)):
    return to_out(db, get_event(db, eid), user)


@router.get("/{eid}/participants", response_model=list[ParticipantOut])
def participants(eid: int, db: Session = Depends(get_db)):
    return [p for p in get_event(db, eid).participants if p.status != "cancelled"]


@router.post("/{eid}/register", response_model=EventOut)
def register(eid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """FR-17: запись с ограничением по максимуму участников."""
    e = get_event(db, eid)
    if e.status not in ("planned", "funded"):
        raise HTTPException(400, "Регистрация на это мероприятие закрыта")
    rec = db.scalar(select(EventParticipant).where(EventParticipant.event_id == eid, EventParticipant.user_id == user.id))
    if rec and rec.status != "cancelled":
        raise HTTPException(400, "Вы уже записаны")
    if active_count(db, eid) >= e.max_participants:
        raise HTTPException(400, "Достигнуто максимальное число участников")
    if rec:
        rec.status = "registered"
        rec.registered_at = datetime.now(timezone.utc)
    else:
        db.add(EventParticipant(event_id=eid, user_id=user.id))
    notify(db, [user.id], "event_registered", f"Вы записаны на «{e.title}»",
           f"Дата: {e.starts_at:%d.%m.%Y %H:%M}. Место: {e.address}", f"/events/{e.id}")
    db.commit()
    return to_out(db, e, user)


@router.post("/{eid}/cancel", response_model=EventOut)
def cancel(eid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    e = get_event(db, eid)
    rec = db.scalar(select(EventParticipant).where(EventParticipant.event_id == eid, EventParticipant.user_id == user.id))
    if not rec or rec.status == "cancelled":
        raise HTTPException(400, "Вы не записаны на это мероприятие")
    rec.status = "cancelled"
    db.commit()
    return to_out(db, e, user)


@router.post("/{eid}/attendance/{participant_id}", response_model=ParticipantOut)
def mark_attended(eid: int, participant_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """FR-11: учёт фактического участия."""
    e = get_event(db, eid)
    if user.id != e.organizer_id and user.role != "admin":
        raise HTTPException(403, "Только организатор")
    rec = db.get(EventParticipant, participant_id)
    if not rec or rec.event_id != eid:
        raise HTTPException(404, "Участник не найден")
    rec.status = "attended"
    db.commit()
    return rec


@router.patch("/{eid}", response_model=EventOut)
def update_event(eid: int, data: EventIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Изменение даты/места → уведомление участникам (FR-11)."""
    e = get_event(db, eid)
    if user.id != e.organizer_id and user.role != "admin":
        raise HTTPException(403, "Только организатор")
    changed = e.starts_at != data.starts_at or e.address != data.address
    for k in ("title", "description", "address", "starts_at", "works", "max_participants", "planned_result"):
        setattr(e, k, getattr(data, k))
    if data.lat and data.lng:
        e.lat, e.lng = data.lat, data.lng
    if changed:
        notify(db, participant_ids(e), "event_changed", f"Изменения в мероприятии «{e.title}»",
               f"Новая дата: {e.starts_at:%d.%m.%Y %H:%M}. Место: {e.address}", f"/events/{e.id}")
    db.commit()
    return to_out(db, e, user)


@router.post("/{eid}/status", response_model=EventOut)
def change_status(eid: int, data: EventStatusIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """FR-18: смена статуса мероприятия и синхронизация статуса проблемы."""
    e = get_event(db, eid)
    if user.id != e.organizer_id and user.role != "admin":
        raise HTTPException(403, "Только организатор")
    if data.status not in EVENT_TRANSITIONS.get(e.status, set()):
        raise HTTPException(400, f"Недопустимый переход {e.status} → {data.status}")
    if data.status == "completed":
        if not (data.result_report or e.result_report):
            raise HTTPException(400, "Для завершения нужен отчёт о результате")
        e.completed_at = datetime.now(timezone.utc)
    if data.result_report:
        e.result_report = data.result_report
    e.status = data.status
    if data.status in PROBLEM_STATUS_BY_EVENT:
        e.problem.status = PROBLEM_STATUS_BY_EVENT[data.status]
    if data.status == "cancelled" and e.problem.status == "planned":
        e.problem.status = "confirmed"
    notify(db, participant_ids(e), "event_status", f"Мероприятие «{e.title}»: статус обновлён",
           e.result_report or "", f"/events/{e.id}")
    db.add(AuditLog(user_id=user.id, action=f"event_status:{data.status}", entity="event", entity_id=e.id))
    db.commit()
    return to_out(db, e, user)
