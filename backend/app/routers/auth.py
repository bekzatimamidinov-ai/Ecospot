from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import AuditLog, User
from ..schemas import LoginIn, RegisterIn, TokenOut, UserOut
from ..security import create_token, get_current_user, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["Авторизация"])


def user_out(u: User) -> UserOut:
    out = UserOut.model_validate(u)
    out.district_ids = [d.id for d in u.districts]
    return out


def token_for(u: User) -> TokenOut:
    return TokenOut(access_token=create_token(u.id), user=user_out(u))


@router.post("/register", response_model=TokenOut, status_code=201)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    email = data.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(400, "Пользователь с такой почтой уже зарегистрирован")
    u = User(name=data.name.strip(), email=email, password_hash=hash_password(data.password))
    db.add(u)
    db.flush()
    db.add(AuditLog(user_id=u.id, action="register", entity="user", entity_id=u.id))
    db.commit()
    return token_for(u)


def _authenticate(db: Session, email: str, password: str) -> User:
    u = db.scalar(select(User).where(User.email == email.lower()))
    if not u or not verify_password(password, u.password_hash):
        raise HTTPException(401, "Неверная почта или пароль")
    if not u.is_active:
        raise HTTPException(403, "Аккаунт заблокирован")
    return u


@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    return token_for(_authenticate(db, data.email, data.password))


@router.post("/token", include_in_schema=False)
def token(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Для кнопки Authorize в Swagger UI."""
    return {"access_token": create_token(_authenticate(db, form.username, form.password).id), "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user_out(user)
