"""FR-10, FR-11, FR-17, FR-18, UC-03. Волонтёрские мероприятия."""
from conftest import ADMIN, MOD_LENINSKY, ORGANIZER, USER

CONFIRMED_PROBLEM_ID = 2  # «Переполненные контейнеры на Токтогула» — подтверждена в демо-данных


def make_event(client, h, **extra):
    body = {"title": "Уборка двора", "description": "Собираем мусор всем двором", "problem_id": CONFIRMED_PROBLEM_ID,
            "type": "volunteer", "address": "ул. Токтогула, 120", "starts_at": "2030-05-01T10:00:00+06:00",
            "works": ["Сбор мусора", "Покраска урн"], "max_participants": 2, "planned_result": "Чистый двор", **extra}
    return client.post("/api/events", json=body, headers=h)


def test_организатор_создаёт_волонтёрское_мероприятие(client, auth):
    r = make_event(client, auth(ORGANIZER))
    assert r.status_code == 201
    e = r.json()
    assert e["status"] == "planned" and e["type"] == "volunteer"
    assert e["works"] == ["Сбор мусора", "Покраска урн"]
    # проблема переходит в статус «Запланирована к устранению»
    assert client.get(f"/api/problems/{CONFIRMED_PROBLEM_ID}").json()["status"] == "planned"


def test_обычный_пользователь_не_может_создать_мероприятие(client, auth):
    assert make_event(client, auth(USER)).status_code == 403


def test_мероприятие_только_для_подтверждённой_проблемы(client, auth, new_problem):
    p = new_problem()  # pending
    assert make_event(client, auth(ORGANIZER), problem_id=p["id"]).status_code == 400


def test_запись_и_отмена_участия(client, auth):
    e = make_event(client, auth(ORGANIZER)).json()
    h = auth(USER)
    r = client.post(f"/api/events/{e['id']}/register", headers=h).json()
    assert r["registered_by_me"] and r["participants_count"] == 1
    assert client.post(f"/api/events/{e['id']}/register", headers=h).status_code == 400  # повторно нельзя
    r = client.post(f"/api/events/{e['id']}/cancel", headers=h).json()
    assert not r["registered_by_me"] and r["participants_count"] == 0


def test_лимит_участников(client, auth):
    e = make_event(client, auth(ORGANIZER), max_participants=2).json()
    assert client.post(f"/api/events/{e['id']}/register", headers=auth(USER)).status_code == 200
    assert client.post(f"/api/events/{e['id']}/register", headers=auth(MOD_LENINSKY)).status_code == 200
    r = client.post(f"/api/events/{e['id']}/register", headers=auth(ADMIN))
    assert r.status_code == 400 and "максимальное" in r.json()["detail"]


def test_список_участников(client, auth):
    e = make_event(client, auth(ORGANIZER)).json()
    client.post(f"/api/events/{e['id']}/register", headers=auth(USER))
    names = [p["user"]["name"] for p in client.get(f"/api/events/{e['id']}/participants").json()]
    assert names == ["Бекзат Житель"]


def test_уведомление_участникам_при_изменении_даты(client, auth):
    h_org = auth(ORGANIZER)
    e = make_event(client, h_org).json()
    client.post(f"/api/events/{e['id']}/register", headers=auth(USER))
    body = {k: e[k] for k in ("title", "description", "problem_id", "type", "address", "works", "max_participants", "planned_result")}
    client.patch(f"/api/events/{e['id']}", json={**body, "starts_at": "2030-05-02T12:00:00+06:00"}, headers=h_org)
    notes = client.get("/api/notifications", headers=auth(USER)).json()
    assert any(n["type"] == "event_changed" for n in notes)


def test_полный_цикл_мероприятия_и_устранение_проблемы(client, auth):
    h = auth(ORGANIZER)
    e = make_event(client, h).json()
    client.post(f"/api/events/{e['id']}/register", headers=auth(USER))

    r = client.post(f"/api/events/{e['id']}/status", json={"status": "in_progress"}, headers=h)
    assert r.json()["status"] == "in_progress"
    assert client.get(f"/api/problems/{CONFIRMED_PROBLEM_ID}").json()["status"] == "in_progress"

    # учёт фактического участия
    part = client.get(f"/api/events/{e['id']}/participants").json()[0]
    assert client.post(f"/api/events/{e['id']}/attendance/{part['id']}", headers=h).json()["status"] == "attended"

    # без отчёта завершить нельзя
    assert client.post(f"/api/events/{e['id']}/status", json={"status": "completed"}, headers=h).status_code == 400
    r = client.post(f"/api/events/{e['id']}/status", json={"status": "completed", "result_report": "Вывезено 40 мешков"}, headers=h)
    assert r.json()["status"] == "completed" and r.json()["completed_at"]
    assert client.get(f"/api/problems/{CONFIRMED_PROBLEM_ID}").json()["status"] == "resolved"


def test_недопустимый_переход_статуса(client, auth):
    h = auth(ORGANIZER)
    e = make_event(client, h).json()
    assert client.post(f"/api/events/{e['id']}/status", json={"status": "completed", "result_report": "x"}, headers=h).status_code == 400


def test_чужой_пользователь_не_управляет_мероприятием(client, auth):
    e = make_event(client, auth(ORGANIZER)).json()
    assert client.post(f"/api/events/{e['id']}/status", json={"status": "cancelled"}, headers=auth(USER)).status_code == 403


def test_отмена_мероприятия_возвращает_проблему_в_подтверждённые(client, auth):
    h = auth(ORGANIZER)
    e = make_event(client, h).json()
    client.post(f"/api/events/{e['id']}/status", json={"status": "cancelled"}, headers=h)
    assert client.get(f"/api/problems/{CONFIRMED_PROBLEM_ID}").json()["status"] == "confirmed"
