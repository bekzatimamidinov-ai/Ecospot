"""Общие фикстуры автотестов.

Тесты работают на отдельной базе ecospot_test, рабочая база не затрагивается.
Перед каждым тестом база пересоздаётся и заполняется демо-данными.
"""
import os

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://ecospot:ecospot@127.0.0.1:5433/ecospot_test")

import bcrypt  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

# Ускоряем хеширование паролей в тестах
_gensalt = bcrypt.gensalt
bcrypt.gensalt = lambda rounds=4, prefix=b"2b": _gensalt(4, prefix)

from app.main import app  # noqa: E402
from app.seed import DEMO_PASSWORD, run  # noqa: E402

ADMIN = "admin@ecospot.kg"
MOD_LENINSKY = "mod.leninsky@ecospot.kg"      # Ленинский, Первомайский
MOD_OKTYABRSKY = "mod.oktyabrsky@ecospot.kg"  # Октябрьский, Свердловский
ORGANIZER = "organizer@ecospot.kg"
USER = "user@ecospot.kg"

# Точка в Ленинском районе
LENINSKY_POINT = {"lat": 42.8590, "lng": 74.5560}


@pytest.fixture(autouse=True)
def fresh_db():
    run(reset=True)
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth(client):
    """auth(email) -> заголовки с JWT-токеном пользователя."""
    def _auth(email: str) -> dict:
        r = client.post("/api/auth/login", json={"email": email, "password": DEMO_PASSWORD})
        assert r.status_code == 200, r.text
        return {"Authorization": f"Bearer {r.json()['access_token']}"}
    return _auth


@pytest.fixture
def new_problem(client, auth):
    """Создаёт сообщение о проблеме от жителя в Ленинском районе."""
    def _create(**extra) -> dict:
        body = {"title": "Свалка во дворе", "description": "Мешки с мусором лежат третий день",
                "category_id": 1, **LENINSKY_POINT, "address": "ул. Тестовая, 1", **extra}
        r = client.post("/api/problems", json=body, headers=auth(USER))
        assert r.status_code == 201, r.text
        return r.json()
    return _create
