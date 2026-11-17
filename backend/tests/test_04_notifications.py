"""FR-09, UC-05. Уведомления и подписки."""
from conftest import ADMIN, MOD_LENINSKY, MOD_OKTYABRSKY, ORGANIZER, USER


def titles(client, h):
    return [n["title"] for n in client.get("/api/notifications", headers=h).json()]


def test_модератор_района_получает_уведомление_о_новом_сообщении(client, auth, new_problem):
    new_problem()
    assert any("на проверку" in t for t in titles(client, auth(MOD_LENINSKY)))
    assert not any("на проверку" in t for t in titles(client, auth(MOD_OKTYABRSKY)))


def test_подписчик_района_получает_уведомление_с_пометкой_не_проверено(client, auth, new_problem):
    h = auth(ORGANIZER)
    client.put("/api/subscriptions", json={"district_ids": [1], "category_ids": []}, headers=h)
    p = new_problem()
    notes = client.get("/api/notifications", headers=h).json()
    n = next(n for n in notes if n["type"] == "new_problem")
    assert "ещё не проверено" in n["title"]
    assert "Ленинский" in n["body"] and "Незаконная свалка" in n["body"]
    assert n["link"] == f"/problems/{p['id']}"


def test_подписка_по_категории(client, auth, new_problem):
    h = auth(ORGANIZER)
    client.put("/api/subscriptions", json={"district_ids": [], "category_ids": [3]}, headers=h)
    new_problem(category_id=1)
    assert not any(n["type"] == "new_problem" for n in client.get("/api/notifications", headers=h).json())
    new_problem(category_id=3, title="Нефть в арыке")
    assert any(n["type"] == "new_problem" for n in client.get("/api/notifications", headers=h).json())


def test_без_подписки_уведомлений_нет(client, auth, new_problem):
    new_problem()
    assert not any(n["type"] == "new_problem" for n in client.get("/api/notifications", headers=auth(ORGANIZER)).json())


def test_автор_получает_результат_проверки_с_причиной(client, auth, new_problem):
    p = new_problem()
    client.post(f"/api/problems/{p['id']}/moderate", json={"action": "reject", "comment": "Не найдено на месте"},
                headers=auth(MOD_LENINSKY))
    n = client.get("/api/notifications", headers=auth(USER)).json()[0]
    assert n["type"] == "moderation_result"
    assert "Отклонена" in n["title"] and "Не найдено на месте" in n["body"]


def test_управление_подписками(client, auth):
    h = auth(USER)
    r = client.put("/api/subscriptions", json={"district_ids": [2, 3], "category_ids": [1]}, headers=h)
    assert r.json() == {"district_ids": [2, 3], "category_ids": [1]}
    client.put("/api/subscriptions", json={"district_ids": [], "category_ids": []}, headers=h)
    assert client.get("/api/subscriptions", headers=h).json() == {"district_ids": [], "category_ids": []}


def test_прочтение_уведомлений(client, auth, new_problem):
    new_problem()
    h = auth(MOD_LENINSKY)
    assert client.get("/api/notifications/unread-count", headers=h).json()["count"] >= 1
    client.post("/api/notifications/read-all", headers=h)
    assert client.get("/api/notifications/unread-count", headers=h).json()["count"] == 0


def test_общая_рассылка_администратора(client, auth):
    r = client.post("/api/notifications/broadcast", json={"title": "Субботник в субботу"}, headers=auth(ADMIN))
    assert r.json()["sent"] == 5
    assert "Субботник в субботу" in titles(client, auth(USER))
    assert client.post("/api/notifications/broadcast", json={"title": "x"}, headers=auth(USER)).status_code == 403
