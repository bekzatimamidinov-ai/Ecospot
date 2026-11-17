"""FR-01. Регистрация и авторизация. NFR-04. Безопасность."""
from sqlalchemy import select

from app.db import SessionLocal
from app.models import User


def test_регистрация_нового_пользователя(client):
    r = client.post("/api/auth/register", json={"name": "Асель", "email": "asel@mail.kg", "password": "secret1"})
    assert r.status_code == 201
    data = r.json()
    assert data["access_token"]
    assert data["user"]["role"] == "user"


def test_пароль_хранится_в_виде_хеша(client):
    client.post("/api/auth/register", json={"name": "Асель", "email": "asel@mail.kg", "password": "secret1"})
    with SessionLocal() as db:
        u = db.scalar(select(User).where(User.email == "asel@mail.kg"))
    assert u.password_hash != "secret1"
    assert u.password_hash.startswith("$2b$")


def test_повторная_регистрация_с_той_же_почтой_запрещена(client):
    body = {"name": "Асель", "email": "asel@mail.kg", "password": "secret1"}
    client.post("/api/auth/register", json=body)
    assert client.post("/api/auth/register", json=body).status_code == 400


def test_некорректные_данные_при_регистрации(client):
    assert client.post("/api/auth/register", json={"name": "А", "email": "не-почта", "password": "1"}).status_code == 422


def test_вход_с_верным_паролем(client):
    r = client.post("/api/auth/login", json={"email": "user@ecospot.kg", "password": "ecospot123"})
    assert r.status_code == 200
    assert r.json()["user"]["email"] == "user@ecospot.kg"


def test_вход_с_неверным_паролем(client):
    r = client.post("/api/auth/login", json={"email": "user@ecospot.kg", "password": "wrong-pass"})
    assert r.status_code == 401


def test_профиль_доступен_только_с_токеном(client, auth):
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer fake-token"}).status_code == 401
    assert client.get("/api/auth/me", headers=auth("user@ecospot.kg")).status_code == 200
