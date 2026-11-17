"""FR-02 – FR-04, FR-07, FR-08, FR-19. Карта, создание проблемы, поддержка, поиск."""
from conftest import USER, ORGANIZER, MOD_LENINSKY

PNG_1x1 = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
    "1f15c4890000000d49444154789c6300010000000500010d0a2db40000000049454e44ae426082"
)


def test_гость_видит_проблемы_на_карте(client):
    r = client.get("/api/problems")
    assert r.status_code == 200
    items = r.json()
    assert len(items) > 0
    assert all("lat" in p and "lng" in p and "status" in p and "category" in p for p in items)


def test_гость_не_может_создать_проблему(client):
    r = client.post("/api/problems", json={"title": "x" * 5, "description": "y" * 20, "category_id": 1, "lat": 42.86, "lng": 74.6})
    assert r.status_code == 401


def test_новая_проблема_получает_статус_ожидает_проверки(new_problem):
    p = new_problem()
    assert p["status"] == "pending"
    assert p["history"][0]["new_status"] == "pending"


def test_район_определяется_автоматически_по_координатам(new_problem):
    p = new_problem()  # точка в Ленинском районе
    assert p["district"]["name"] == "Ленинский"


def test_район_можно_выбрать_вручную(new_problem):
    p = new_problem(district_id=3)
    assert p["district"]["id"] == 3


def test_координаты_вне_бишкека_отклоняются(client, auth):
    body = {"title": "Свалка", "description": "Описание проблемы", "category_id": 1, "lat": 40.5, "lng": 72.8}
    assert client.post("/api/problems", json=body, headers=auth(USER)).status_code == 422


def test_загрузка_фотографии(client, auth, new_problem):
    p = new_problem()
    r = client.post(f"/api/problems/{p['id']}/photos", headers=auth(USER),
                    files=[("files", ("photo.png", PNG_1x1, "image/png"))])
    assert r.status_code == 200
    assert client.get(f"/api/problems/{p['id']}").json()["photos"] == r.json()


def test_загрузка_не_изображения_запрещена(client, auth, new_problem):
    p = new_problem()
    r = client.post(f"/api/problems/{p['id']}/photos", headers=auth(USER),
                    files=[("files", ("virus.exe", b"MZ...", "application/octet-stream"))])
    assert r.status_code == 400


def test_поддержка_проблемы_учитывается_один_раз(client, auth, new_problem):
    p = new_problem()
    h = auth(ORGANIZER)
    r1 = client.post(f"/api/problems/{p['id']}/support", headers=h).json()
    assert r1 == {"supported": True, "supports_count": 1}
    # повторное нажатие снимает поддержку, а не добавляет вторую
    r2 = client.post(f"/api/problems/{p['id']}/support", headers=h).json()
    assert r2 == {"supported": False, "supports_count": 0}


def test_поддержки_разных_пользователей_суммируются(client, auth, new_problem):
    p = new_problem()
    for email in (USER, ORGANIZER, MOD_LENINSKY):
        client.post(f"/api/problems/{p['id']}/support", headers=auth(email))
    assert client.get(f"/api/problems/{p['id']}").json()["supports_count"] == 3


def test_комментарии_к_проблеме(client, auth, new_problem):
    p = new_problem()
    client.post(f"/api/problems/{p['id']}/comments", json={"text": "Подтверждаю, видел сам"}, headers=auth(ORGANIZER))
    comments = client.get(f"/api/problems/{p['id']}/comments").json()
    assert comments[0]["text"] == "Подтверждаю, видел сам"


def test_поиск_по_названию_и_адресу(client):
    assert {p["title"] for p in client.get("/api/problems", params={"q": "Ала-Арч"}).json()} == {"Свалка у русла Ала-Арчи"}
    assert len(client.get("/api/problems", params={"q": "Токтогула"}).json()) == 1


def test_фильтры_по_району_категории_статусу(client):
    leninsky = client.get("/api/problems", params={"district_id": 1}).json()
    assert leninsky and all(p["district"]["id"] == 1 for p in leninsky)
    water = client.get("/api/problems", params={"category_id": 3}).json()
    assert water and all(p["category"]["id"] == 3 for p in water)
    resolved = client.get("/api/problems", params={"status": "resolved"}).json()
    assert resolved and all(p["status"] == "resolved" for p in resolved)


def test_отклонённые_сообщения_не_видны_гостю(client, auth, new_problem):
    p = new_problem()
    client.post(f"/api/problems/{p['id']}/moderate", json={"action": "reject", "comment": "Фейк"}, headers=auth(MOD_LENINSKY))
    assert p["id"] not in [x["id"] for x in client.get("/api/problems").json()]
    assert client.get(f"/api/problems/{p['id']}").status_code == 404
    # а автор своё сообщение видит
    assert client.get(f"/api/problems/{p['id']}", headers=auth(USER)).status_code == 200
