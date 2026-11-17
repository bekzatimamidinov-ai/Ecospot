"""ORM-модели EcoSpot (раздел 11 ТЗ «Требования к данным»)."""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text,
    UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base

# --- Справочники статусов (раздел 8 ТЗ) ---
ROLES = ("user", "organizer", "moderator", "admin", "sponsor", "executor")
PROBLEM_STATUSES = (
    "pending",       # Ожидает проверки
    "extra_check",   # На дополнительной проверке
    "confirmed",     # Подтверждена
    "planned",       # Запланирована к устранению
    "in_progress",   # В процессе устранения
    "resolved",      # Устранена
    "rejected",      # Отклонена
    "duplicate",     # Дубликат
)
EVENT_TYPES = ("volunteer", "funded")
EVENT_STATUSES = (
    "draft", "awaiting_approval", "planned", "fundraising", "funded",
    "in_progress", "awaiting_review", "completed", "cancelled",
)
PAYMENT_STATUSES = ("created", "pending", "confirmed", "declined", "refunded")
PAYOUT_STATUSES = ("awaiting_review", "awaiting_payout", "initiated", "paid", "error", "returned")


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ModeratorDistrict(Base):
    __tablename__ = "moderator_districts"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    district_id: Mapped[int] = mapped_column(ForeignKey("districts.id", ondelete="CASCADE"), primary_key=True)


class User(TimestampMixin, Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    districts: Mapped[list["District"]] = relationship(secondary="moderator_districts", back_populates="moderators")


class District(Base):
    __tablename__ = "districts"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    center_lat: Mapped[float]
    center_lng: Mapped[float]
    boundary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # GeoJSON-полигон

    moderators: Mapped[list[User]] = relationship(secondary="moderator_districts", back_populates="districts")


class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    color: Mapped[str] = mapped_column(String(7), default="#2e7d32")


class Problem(TimestampMixin, Base):
    __tablename__ = "problems"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    district_id: Mapped[int] = mapped_column(ForeignKey("districts.id"), index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    lat: Mapped[float]
    lng: Mapped[float]
    address: Mapped[str] = mapped_column(String(300), default="")
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    priority: Mapped[int] = mapped_column(Integer, default=2)  # 1 высокий, 2 средний, 3 низкий
    discovered_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    category: Mapped[Category] = relationship()
    district: Mapped[District] = relationship()
    author: Mapped[User] = relationship()
    photos: Mapped[list["ProblemPhoto"]] = relationship(cascade="all, delete-orphan")
    history: Mapped[list["ModerationHistory"]] = relationship(cascade="all, delete-orphan", order_by="ModerationHistory.created_at")
    events: Mapped[list["Event"]] = relationship(back_populates="problem")


class ProblemPhoto(TimestampMixin, Base):
    __tablename__ = "problem_photos"
    id: Mapped[int] = mapped_column(primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id", ondelete="CASCADE"))
    url: Mapped[str] = mapped_column(String(300))


class ProblemSupport(TimestampMixin, Base):
    """FR-08: один пользователь — одна поддержка."""
    __tablename__ = "problem_supports"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id", ondelete="CASCADE"), primary_key=True)


class ProblemComment(TimestampMixin, Base):
    __tablename__ = "problem_comments"
    id: Mapped[int] = mapped_column(primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    text: Mapped[str] = mapped_column(Text)
    user: Mapped[User] = relationship()


class ModerationHistory(TimestampMixin, Base):
    """NFR-06: история проверки и смены статусов."""
    __tablename__ = "moderation_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id", ondelete="CASCADE"), index=True)
    moderator_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    old_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    new_status: Mapped[str] = mapped_column(String(20))
    comment: Mapped[str] = mapped_column(Text, default="")
    moderator: Mapped[User | None] = relationship()


class Event(TimestampMixin, Base):
    __tablename__ = "events"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"))
    organizer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    type: Mapped[str] = mapped_column(String(20), default="volunteer")
    address: Mapped[str] = mapped_column(String(300))
    lat: Mapped[float]
    lng: Mapped[float]
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    works: Mapped[list[str]] = mapped_column(JSONB, default=list)
    max_participants: Mapped[int] = mapped_column(Integer, default=20)
    planned_result: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="planned", index=True)
    result_report: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Поля финансируемого мероприятия (этап 2)
    goal_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    fundraising_deadline: Mapped[date | None] = mapped_column(Date, nullable=True)

    problem: Mapped[Problem] = relationship(back_populates="events")
    organizer: Mapped[User] = relationship()
    participants: Mapped[list["EventParticipant"]] = relationship(cascade="all, delete-orphan")


class EventParticipant(Base):
    __tablename__ = "event_participants"
    __table_args__ = (UniqueConstraint("event_id", "user_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(20), default="registered")  # registered|cancelled|attended
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    user: Mapped[User] = relationship()


class Subscription(TimestampMixin, Base):
    """FR-09: подписка на район и/или категорию."""
    __tablename__ = "subscriptions"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    district_id: Mapped[int | None] = mapped_column(ForeignKey("districts.id", ondelete="CASCADE"), nullable=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"), nullable=True)


class Notification(TimestampMixin, Base):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(String(40))
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text, default="")
    link: Mapped[str | None] = mapped_column(String(300), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)


# ---------- Финансовый блок (этап 2: таблицы созданы, API в разработке) ----------

class EstimateItem(Base):
    """Строка сметы (FR-12)."""
    __tablename__ = "estimate_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(20))  # works|materials|equipment|transport|other
    title: Mapped[str] = mapped_column(String(200))
    planned_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    approved_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)


class Donation(TimestampMixin, Base):
    """Спонсорский взнос (FR-13, FR-14)."""
    __tablename__ = "donations"
    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"))
    sponsor_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    status: Mapped[str] = mapped_column(String(20), default="created")
    provider_ref: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False)


class Payout(TimestampMixin, Base):
    """Выплата исполнителю (FR-15)."""
    __tablename__ = "payouts"
    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"))
    executor_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    status: Mapped[str] = mapped_column(String(20), default="awaiting_review")
    documents: Mapped[list[str]] = mapped_column(JSONB, default=list)


class AuditLog(TimestampMixin, Base):
    """Журнал действий (FR-21)."""
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(60))
    entity: Mapped[str] = mapped_column(String(40))
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
