import math
import uuid
from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from ..config import settings
from ..db import get_db
from ..models import (
    AuditLog, Category, District, ModerationHistory, Problem, ProblemComment,
    ProblemPhoto, ProblemSupport, User,
)
from ..notify import notify_moderation_result, notify_new_problem
from ..schemas import (
    CommentIn, CommentOut, ModerationIn, ProblemDetail, ProblemIn, ProblemListItem,
)
from ..security import get_current_user, get_current_user_optional, require_roles

router = APIRouter(prefix="/api/problems", tags=["Экологические проблемы"])

PUBLIC_STATUSES = ("pending", "extra_check", "confirmed", "planned", "in_progress", "resolved")
ALLOWED_IMAGE = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


def nearest_district(db: Session, lat: float, lng: float) -> District:
    """FR-03: автоопределение района по ближайшему центру."""
    districts = db.scalars(select(District)).all()
    return min(districts, key=lambda d: math.hypot(d.center_lat - lat, d.center_lng - lng))


def supports_count(db: Session, pid: int) -> int:
    return db.scalar(select(func.count()).select_from(ProblemSupport).where(ProblemSupport.problem_id == pid)) or 0


def to_list_item(db: Session, p: Problem) -> ProblemListItem:
    item = ProblemListItem.model_validate(p)
    item.supports_count = supports_count(db, p.id)
    item.photo = p.photos[0].url if p.photos else None
    return item


def can_moderate(user: User | None, p: Problem) -> bool:
    if user is None:
        return False
    if user.role == "admin":
        return True
    return user.role == "moderator" and p.district_id in {d.id for d in user.districts}


def get_problem(db: Session, pid: int) -> Problem:
    p = db.get(Problem, pid)
    if not p:
        raise HTTPException(404, "Проблема не найдена")
    return p


@router.get("", response_model=list[ProblemListItem])
def list_problems(
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
    q: str | None = None,
    district_id: int | None = None,
    category_id: int | None = None,
    status: list[str] | None = Query(None),
    priority: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    mine: bool = False,
    limit: int = Query(200, le=500),
):
    """FR-19: поиск по названию/адресу, фильтры по району, категории, статусу, дате, приоритету."""
    stmt = select(Problem).options(
        selectinload(Problem.photos), selectinload(Problem.category), selectinload(Problem.district)
    )
    if mine and user:
        stmt = stmt.where(Problem.author_id == user.id)
    elif status:
        allowed = set(status)
        if not (user and user.role in ("moderator", "admin")):
            allowed &= set(PUBLIC_STATUSES)
        stmt = stmt.where(Problem.status.in_(allowed))
    else:
        stmt = stmt.where(Problem.status.in_(PUBLIC_STATUSES))
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Problem.title.ilike(like), Problem.address.ilike(like)))
    if district_id:
        stmt = stmt.where(Problem.district_id == district_id)
    if category_id:
        stmt = stmt.where(Problem.category_id == category_id)
    if priority:
        stmt = stmt.where(Problem.priority == priority)
    if date_from:
        stmt = stmt.where(func.date(Problem.created_at) >= date_from)
    if date_to:
        stmt = stmt.where(func.date(Problem.created_at) <= date_to)
    rows = db.scalars(stmt.order_by(Problem.created_at.desc()).limit(limit)).all()
    return [to_list_item(db, p) for p in rows]


@router.get("/supported", response_model=list[ProblemListItem])
def supported(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(
        select(Problem).join(ProblemSupport, ProblemSupport.problem_id == Problem.id)
        .where(ProblemSupport.user_id == user.id)
    ).all()
    return [to_list_item(db, p) for p in rows]


@router.post("", response_model=ProblemDetail, status_code=201)
def create_problem(data: ProblemIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not db.get(Category, data.category_id):
        raise HTTPException(400, "Неизвестная категория")
    district = db.get(District, data.district_id) if data.district_id else nearest_district(db, data.lat, data.lng)
    if not district:
        raise HTTPException(400, "Неизвестный район")
    p = Problem(**data.model_dump(exclude={"district_id"}), district_id=district.id, author_id=user.id, status="pending")
    db.add(p)
    db.flush()
    db.add(ModerationHistory(problem_id=p.id, new_status="pending", comment="Сообщение создано"))
    db.add(AuditLog(user_id=user.id, action="create", entity="problem", entity_id=p.id))
    db.refresh(p)
    notify_new_problem(db, p)
    db.commit()
    return detail(p.id, db, user)


@router.get("/{pid}", response_model=ProblemDetail)
def detail(pid: int, db: Session = Depends(get_db), user: User | None = Depends(get_current_user_optional)):
    p = get_problem(db, pid)
    if p.status not in PUBLIC_STATUSES and not (user and (user.id == p.author_id or can_moderate(user, p))):
        raise HTTPException(404, "Проблема не найдена")
    d = ProblemDetail.model_validate(p)
    d.supports_count = supports_count(db, p.id)
    d.photos = [ph.url for ph in p.photos]
    d.photo = d.photos[0] if d.photos else None
    if user:
        d.supported_by_me = db.get(ProblemSupport, (user.id, p.id)) is not None
    return d


@router.post("/{pid}/photos", response_model=list[str])
async def upload_photos(pid: int, files: list[UploadFile] = File(...), db: Session = Depends(get_db),
                        user: User = Depends(get_current_user)):
    p = get_problem(db, pid)
    if p.author_id != user.id and not can_moderate(user, p):
        raise HTTPException(403, "Добавлять фото может только автор")
    urls = []
    for f in files[:10]:
        ext = ALLOWED_IMAGE.get(f.content_type or "")
        if not ext:
            raise HTTPException(400, f"Неподдерживаемый формат: {f.filename}")
        content = await f.read()
        if len(content) > 8 * 1024 * 1024:
            raise HTTPException(400, "Файл больше 8 МБ")
        name = f"{uuid.uuid4().hex}{ext}"
        (settings.upload_dir / name).write_bytes(content)
        url = f"/uploads/{name}"
        db.add(ProblemPhoto(problem_id=p.id, url=url))
        urls.append(url)
    db.commit()
    return urls


@router.post("/{pid}/support")
def support(pid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """FR-08: повторная поддержка не допускается — повторный вызов снимает поддержку."""
    p = get_problem(db, pid)
    existing = db.get(ProblemSupport, (user.id, p.id))
    if existing:
        db.delete(existing)
    else:
        db.add(ProblemSupport(user_id=user.id, problem_id=p.id))
    db.commit()
    return {"supported": existing is None, "supports_count": supports_count(db, p.id)}


@router.get("/{pid}/comments", response_model=list[CommentOut])
def comments(pid: int, db: Session = Depends(get_db)):
    return db.scalars(select(ProblemComment).where(ProblemComment.problem_id == pid).order_by(ProblemComment.created_at)).all()


@router.post("/{pid}/comments", response_model=CommentOut, status_code=201)
def add_comment(pid: int, data: CommentIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    get_problem(db, pid)
    c = ProblemComment(problem_id=pid, user_id=user.id, text=data.text)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


# ---------------- Модерация (FR-05, UC-02) ----------------

@router.get("/moderation/queue", response_model=list[ProblemListItem], tags=["Модерация"])
def moderation_queue(db: Session = Depends(get_db), user: User = Depends(require_roles("moderator", "admin"))):
    stmt = select(Problem).where(Problem.status.in_(("pending", "extra_check")))
    if user.role != "admin":
        stmt = stmt.where(Problem.district_id.in_([d.id for d in user.districts] or [-1]))
    return [to_list_item(db, p) for p in db.scalars(stmt.order_by(Problem.created_at)).all()]


@router.get("/{pid}/similar", response_model=list[ProblemListItem], tags=["Модерация"])
def similar(pid: int, db: Session = Depends(get_db), user: User = Depends(require_roles("moderator", "admin"))):
    """Поиск возможных дубликатов: та же категория в радиусе ~300 м."""
    p = get_problem(db, pid)
    d = 0.003
    rows = db.scalars(select(Problem).where(
        Problem.id != p.id, Problem.category_id == p.category_id,
        Problem.lat.between(p.lat - d, p.lat + d), Problem.lng.between(p.lng - d, p.lng + d),
        Problem.status.notin_(("rejected", "duplicate")),
    )).all()
    return [to_list_item(db, x) for x in rows]


@router.post("/{pid}/moderate", response_model=ProblemDetail, tags=["Модерация"])
def moderate(pid: int, data: ModerationIn, db: Session = Depends(get_db),
             user: User = Depends(require_roles("moderator", "admin"))):
    p = get_problem(db, pid)
    if not can_moderate(user, p):
        raise HTTPException(403, "Проблема вне закреплённых за вами районов")
    if p.status not in ("pending", "extra_check"):
        raise HTTPException(400, "Сообщение уже проверено")
    new_status = {
        "confirm": "confirmed", "reject": "rejected", "duplicate": "duplicate",
        "extra_check": "extra_check", "request_info": "extra_check",
    }[data.action]
    comment = data.comment.strip()
    if data.action == "reject" and not comment:
        raise HTTPException(400, "Укажите причину отклонения")
    if data.action == "duplicate":
        if not data.duplicate_of or not db.get(Problem, data.duplicate_of):
            raise HTTPException(400, "Укажите номер исходной проблемы")
        comment = f"Дубликат проблемы №{data.duplicate_of}. {comment}".strip()
    if data.action == "request_info":
        comment = f"Запрошены дополнительные сведения: {comment}"
    db.add(ModerationHistory(problem_id=p.id, moderator_id=user.id, old_status=p.status, new_status=new_status, comment=comment))
    db.add(AuditLog(user_id=user.id, action=f"moderate:{data.action}", entity="problem", entity_id=p.id))
    p.status = new_status
    notify_moderation_result(db, p, comment)
    db.commit()
    return detail(p.id, db, user)
