"""FR-06, FR-22. Статистика по районам и общая статистика."""
from conftest import MOD_LENINSKY


def district(client, name):
    return next(d for d in client.get("/api/stats/districts").json() if d["name"] == name)


def test_статистика_по_всем_районам_бишкека(client):
    stats = client.get("/api/stats/districts").json()
    assert {d["name"] for d in stats} == {"Ленинский", "Октябрьский", "Первомайский", "Свердловский"}
    for key in ("new", "on_check", "confirmed", "in_progress", "resolved", "events_planned"):
        assert key in stats[0]


def test_счётчики_района_меняются_после_модерации(client, auth, new_problem):
    before = district(client, "Ленинский")
    p = new_problem()
    assert district(client, "Ленинский")["new"] == before["new"] + 1
    client.post(f"/api/problems/{p['id']}/moderate", json={"action": "confirm"}, headers=auth(MOD_LENINSKY))
    after = district(client, "Ленинский")
    assert after["new"] == before["new"]
    assert after["confirmed"] == before["confirmed"] + 1


def test_общая_статистика(client):
    s = client.get("/api/stats/summary").json()
    assert s["problems_total"] == 7
    assert s["users_total"] == 5
    assert s["by_status"]["resolved"] == 1
    assert sum(c["count"] for c in s["by_category"]) == 7
