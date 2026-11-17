"""Внутренняя система уведомлений (FR-09)."""
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from .models import ModeratorDistrict, Notification, Problem, Subscription, User

STATUS_RU = {
    "pending": "Ожидает проверки",
    "extra_check": "На дополнительной проверке",
    "confirmed": "Подтверждена",
    "planned": "Запланирована к устранению",
    "in_progress": "В процессе устранения",
    "resolved": "Устранена",
    "rejected": "Отклонена",
    "duplicate": "Дубликат",
}


def notify(db: Session, user_ids, type_: str, title: str, body: str = "", link: str | None = None) -> None:
    for uid in set(user_ids):
        db.add(Notification(user_id=uid, type=type_, title=title, body=body, link=link))


def notify_new_problem(db: Session, p: Problem) -> None:
    """UC-01: модераторам района + подписчикам района/категории.
    Непроверенное сообщение не подаётся как факт."""
    link = f"/problems/{p.id}"
    info = (f"Район: {p.district.name}. Категория: {p.category.name}. "
            f"Дата: {p.created_at:%d.%m.%Y}. Статус: {STATUS_RU[p.status]}.")

    mods = set(db.scalars(select(ModeratorDistrict.user_id).where(ModeratorDistrict.district_id == p.district_id)))
    mods |= set(db.scalars(select(User.id).where(User.role == "admin")))
    notify(db, mods - {p.author_id}, "moderation_needed", f"Новое сообщение на проверку: {p.title}", info, link)

    subs = set(db.scalars(
        select(Subscription.user_id).where(or_(
            Subscription.district_id == p.district_id,
            Subscription.category_id == p.category_id,
        ))
    ))
    notify(db, subs - mods - {p.author_id}, "new_problem",
           f"Новое сообщение (ещё не проверено): {p.title}",
           info + " Сообщение пока не подтверждено модератором.", link)


def notify_moderation_result(db: Session, p: Problem, comment: str) -> None:
    text = f"Статус вашего сообщения «{p.title}»: {STATUS_RU[p.status]}."
    if comment:
        text += f" Комментарий модератора: {comment}"
    notify(db, [p.author_id], "moderation_result", f"Результат проверки: {STATUS_RU[p.status]}", text, f"/problems/{p.id}")
