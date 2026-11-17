"""FR-05, FR-06, UC-02. Проверка достоверности сообщений модератором района."""
from conftest import ADMIN, MOD_LENINSKY, MOD_OKTYABRSKY, USER


def moderate(client, h, pid, action, **kw):
    return client.post(f"/api/problems/{pid}/moderate", json={"action": action, **kw}, headers=h)


def test_модератор_видит_очередь_только_своих_районов(client, auth, new_problem):
    p = new_problem()  # Ленинский
    q_len = [x["id"] for x in client.get("/api/problems/moderation/queue", headers=auth(MOD_LENINSKY)).json()]
    q_okt = [x["id"] for x in client.get("/api/problems/moderation/queue", headers=auth(MOD_OKTYABRSKY)).json()]
    assert p["id"] in q_len
    assert p["id"] not in q_okt


def test_администратор_видит_все_районы(client, auth, new_problem):
    p = new_problem()
    q = client.get("/api/problems/moderation/queue", headers=auth(ADMIN)).json()
    assert p["id"] in [x["id"] for x in q]
    assert len({x["district"]["id"] for x in q}) > 1


def test_обычный_пользователь_не_может_модерировать(client, auth, new_problem):
    p = new_problem()
    assert client.get("/api/problems/moderation/queue", headers=auth(USER)).status_code == 403
    assert moderate(client, auth(USER), p["id"], "confirm").status_code == 403


def test_модератор_чужого_района_не_может_проверить(client, auth, new_problem):
    p = new_problem()
    assert moderate(client, auth(MOD_OKTYABRSKY), p["id"], "confirm").status_code == 403


def test_подтверждение_проблемы(client, auth, new_problem):
    p = new_problem()
    r = moderate(client, auth(MOD_LENINSKY), p["id"], "confirm", comment="Проверено по фото")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "confirmed"
    last = data["history"][-1]
    assert (last["old_status"], last["new_status"]) == ("pending", "confirmed")
    assert last["moderator"]["name"] == "Модератор Ленинского"


def test_отклонение_требует_причину(client, auth, new_problem):
    p = new_problem()
    assert moderate(client, auth(MOD_LENINSKY), p["id"], "reject").status_code == 400
    r = moderate(client, auth(MOD_LENINSKY), p["id"], "reject", comment="Мусор уже вывезен")
    assert r.json()["status"] == "rejected"


def test_отметка_дубликата(client, auth, new_problem):
    original = new_problem()
    dup = new_problem(title="Та же свалка")
    assert moderate(client, auth(MOD_LENINSKY), dup["id"], "duplicate").status_code == 400
    r = moderate(client, auth(MOD_LENINSKY), dup["id"], "duplicate", duplicate_of=original["id"])
    assert r.json()["status"] == "duplicate"
    assert f"№{original['id']}" in r.json()["history"][-1]["comment"]


def test_поиск_похожих_сообщений_рядом(client, auth, new_problem):
    a = new_problem()
    b = new_problem(title="Мусор рядом", lat=42.8592, lng=74.5562)
    similar = client.get(f"/api/problems/{b['id']}/similar", headers=auth(MOD_LENINSKY)).json()
    assert a["id"] in [x["id"] for x in similar]


def test_дополнительная_проверка_и_запрос_сведений(client, auth, new_problem):
    p = new_problem()
    r = moderate(client, auth(MOD_LENINSKY), p["id"], "request_info", comment="Пришлите фото ближе")
    assert r.json()["status"] == "extra_check"
    # после доп. проверки сообщение можно подтвердить
    assert moderate(client, auth(MOD_LENINSKY), p["id"], "confirm").json()["status"] == "confirmed"


def test_повторная_модерация_уже_проверенного_запрещена(client, auth, new_problem):
    p = new_problem()
    moderate(client, auth(MOD_LENINSKY), p["id"], "confirm")
    assert moderate(client, auth(MOD_LENINSKY), p["id"], "reject", comment="передумал").status_code == 400


def test_назначение_модератора_на_районы_администратором(client, auth):
    users = client.get("/api/admin/users", headers=auth(ADMIN)).json()
    citizen = next(u for u in users if u["email"] == USER)
    r = client.put(f"/api/admin/users/{citizen['id']}/role", json={"role": "moderator", "district_ids": [2, 4]}, headers=auth(ADMIN))
    assert r.status_code == 200
    assert sorted(r.json()["district_ids"]) == [2, 4]
    # не-админ назначать роли не может
    assert client.get("/api/admin/users", headers=auth(MOD_LENINSKY)).status_code == 403
