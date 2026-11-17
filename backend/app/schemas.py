from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Auth ---
class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(ORM):
    id: int
    name: str
    email: str
    role: str
    created_at: datetime
    district_ids: list[int] = []


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# --- Справочники ---
class DistrictOut(ORM):
    id: int
    name: str
    center_lat: float
    center_lng: float


class CategoryOut(ORM):
    id: int
    name: str
    color: str


# --- Проблемы ---
class ProblemIn(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10)
    category_id: int
    district_id: int | None = None
    lat: float = Field(ge=42.7, le=43.0)
    lng: float = Field(ge=74.4, le=74.8)
    address: str = ""
    discovered_at: date | None = None


class ShortUser(ORM):
    id: int
    name: str


class ProblemListItem(ORM):
    id: int
    title: str
    status: str
    priority: int
    lat: float
    lng: float
    address: str
    created_at: datetime
    category: CategoryOut
    district: DistrictOut
    supports_count: int = 0
    photo: str | None = None


class HistoryOut(ORM):
    id: int
    old_status: str | None
    new_status: str
    comment: str
    created_at: datetime
    moderator: ShortUser | None


class CommentOut(ORM):
    id: int
    text: str
    created_at: datetime
    user: ShortUser


class CommentIn(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class ShortEvent(ORM):
    id: int
    title: str
    type: str
    status: str
    starts_at: datetime


class ProblemDetail(ProblemListItem):
    description: str
    discovered_at: date | None
    author: ShortUser
    photos: list[str] = []
    supported_by_me: bool = False
    history: list[HistoryOut] = []
    events: list[ShortEvent] = []


class ModerationIn(BaseModel):
    action: str = Field(pattern="^(confirm|reject|duplicate|extra_check|request_info)$")
    comment: str = ""
    duplicate_of: int | None = None


class StatusIn(BaseModel):
    status: str
    comment: str = ""


# --- Мероприятия ---
class EventIn(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10)
    problem_id: int
    type: str = Field(default="volunteer", pattern="^(volunteer|funded)$")
    address: str
    lat: float | None = None
    lng: float | None = None
    starts_at: datetime
    works: list[str] = []
    max_participants: int = Field(default=20, ge=1, le=1000)
    planned_result: str = ""


class EventOut(ORM):
    id: int
    title: str
    description: str
    type: str
    status: str
    address: str
    lat: float
    lng: float
    starts_at: datetime
    works: list[str]
    max_participants: int
    planned_result: str
    result_report: str | None
    completed_at: datetime | None
    organizer: ShortUser
    problem_id: int
    problem_title: str = ""
    participants_count: int = 0
    registered_by_me: bool = False


class ParticipantOut(ORM):
    id: int
    status: str
    registered_at: datetime
    user: ShortUser


class EventStatusIn(BaseModel):
    status: str
    result_report: str | None = None


# --- Уведомления ---
class NotificationOut(ORM):
    id: int
    type: str
    title: str
    body: str
    link: str | None
    is_read: bool
    created_at: datetime


class SubscriptionIn(BaseModel):
    district_ids: list[int] = []
    category_ids: list[int] = []


class SubscriptionsOut(BaseModel):
    district_ids: list[int]
    category_ids: list[int]


class BroadcastIn(BaseModel):
    title: str
    body: str = ""
