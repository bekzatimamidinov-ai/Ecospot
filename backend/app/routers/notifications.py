from fastapi import APIRouter, Depends
from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Notification, Subscription, User
from ..notify import notify
from ..schemas import BroadcastIn, NotificationOut, SubscriptionIn, SubscriptionsOut
from ..security import get_current_user, require_roles

router = APIRouter(prefix="/api", tags=["Уведомления"])


@router.get("/notifications", response_model=list[NotificationOut])
def my_notifications(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.scalars(select(Notification).where(Notification.user_id == user.id)
                      .order_by(Notification.created_at.desc()).limit(100)).all()


@router.get("/notifications/unread-count")
def unread_count(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    n = db.scalar(select(func.count()).select_from(Notification).where(
        Notification.user_id == user.id, Notification.is_read.is_(False)))
    return {"count": n or 0}


@router.post("/notifications/read-all")
def read_all(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.execute(update(Notification).where(Notification.user_id == user.id).values(is_read=True))
    db.commit()
    return {"ok": True}


@router.post("/notifications/{nid}/read")
def read_one(nid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.execute(update(Notification).where(Notification.id == nid, Notification.user_id == user.id).values(is_read=True))
    db.commit()
    return {"ok": True}


@router.get("/subscriptions", response_model=SubscriptionsOut)
def get_subscriptions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    subs = db.scalars(select(Subscription).where(Subscription.user_id == user.id)).all()
    return SubscriptionsOut(
        district_ids=[s.district_id for s in subs if s.district_id],
        category_ids=[s.category_id for s in subs if s.category_id],
    )


@router.put("/subscriptions", response_model=SubscriptionsOut)
def set_subscriptions(data: SubscriptionIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """UC-05: сохранение подписок на районы и категории."""
    db.execute(delete(Subscription).where(Subscription.user_id == user.id))
    for d in set(data.district_ids):
        db.add(Subscription(user_id=user.id, district_id=d))
    for c in set(data.category_ids):
        db.add(Subscription(user_id=user.id, category_id=c))
    db.commit()
    return get_subscriptions(db, user)


@router.post("/notifications/broadcast", tags=["Администрирование"])
def broadcast(data: BroadcastIn, db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    """FR-09: общие уведомления от администратора."""
    ids = db.scalars(select(User.id).where(User.is_active.is_(True))).all()
    notify(db, ids, "broadcast", data.title, data.body)
    db.commit()
    return {"sent": len(ids)}
