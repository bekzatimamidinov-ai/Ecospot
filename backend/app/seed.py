"""Создание таблиц и демонстрационных данных.

Запуск:  python -m app.seed          (создать таблицы и заполнить, если пусто)
         python -m app.seed --reset  (удалить всё и создать заново)
"""
import sys
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select

from .db import Base, SessionLocal, engine
from .models import (
    Category, District, Event, EventParticipant, ModerationHistory, Problem,
    ProblemSupport, Subscription, User,
)
from .security import hash_password

DEMO_PASSWORD = "ecospot123"  # тестовый пароль демо-аккаунтов

DISTRICTS = [
    ("Ленинский", 42.8590, 74.5550),
    ("Октябрьский", 42.8420, 74.6250),
    ("Первомайский", 42.8780, 74.5950),
    ("Свердловский", 42.8800, 74.6450),
]
CATEGORIES = [
    ("Незаконная свалка", "#8d4925"),
    ("Переполненные контейнеры", "#f57c00"),
    ("Загрязнение воды", "#1976d2"),
    ("Загрязнение воздуха", "#616161"),
    ("Повреждение зелёных насаждений", "#388e3c"),
    ("Другое", "#7b1fa2"),
]
USERS = [
    ("Администратор", "admin@ecospot.kg", "admin", []),
    ("Модератор Ленинского", "mod.leninsky@ecospot.kg", "moderator", ["Ленинский", "Первомайский"]),
    ("Модератор Октябрьского", "mod.oktyabrsky@ecospot.kg", "moderator", ["Октябрьский", "Свердловский"]),
    ("Айгуль Организатор", "organizer@ecospot.kg", "organizer", []),
    ("Бекзат Житель", "user@ecospot.kg", "user", []),
]
PROBLEMS = [
    ("Свалка у русла Ала-Арчи", "Строительный и бытовой мусор вдоль берега реки, примерно 30 м.", 0, 0, 42.8455, 74.5650, "ул. Ахунбаева / р. Ала-Арча", "confirmed", 1),
    ("Переполненные контейнеры на Токтогула", "Контейнеры не вывозятся больше недели, мусор лежит рядом.", 1, 2, 42.8720, 74.5980, "ул. Токтогула, 120", "confirmed", 2),
    ("Мусор в Большом Чуйском канале", "Пластиковые бутылки и пакеты в канале возле моста.", 2, 3, 42.8890, 74.6300, "БЧК, мост на ул. Жибек Жолу", "pending", 1),
    ("Вырубка деревьев в сквере", "Спилены несколько здоровых карагачей без объявлений.", 4, 1, 42.8350, 74.6150, "мкр. Асанбай, сквер", "extra_check", 2),
    ("Дым от сжигания мусора", "Каждый вечер жгут мусор на пустыре, сильный запах.", 3, 3, 42.8950, 74.6600, "ж/м Ак-Ордо", "pending", 2),
    ("Свалка шин у гаражей", "Около 100 старых шин сброшено за гаражным кооперативом.", 0, 0, 42.8630, 74.5420, "ул. Фучика", "resolved", 3),
    ("Стихийная свалка у Ошского рынка", "Рыночные отходы выбрасываются прямо на тротуар.", 0, 0, 42.8750, 74.5730, "ул. Бейшеналиевой", "in_progress", 1),
]


def run(reset: bool = False) -> None:
    if reset:
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    db = SessionLocal()
    if db.scalar(select(User).limit(1)):
        print("База уже заполнена — пропускаю (используйте --reset для пересоздания).")
        return

    districts = [District(name=n, center_lat=a, center_lng=b) for n, a, b in DISTRICTS]
    categories = [Category(name=n, color=c) for n, c in CATEGORIES]
    db.add_all(districts + categories)
    db.flush()
    by_name = {d.name: d for d in districts}

    users = []
    for name, email, role, dnames in USERS:
        u = User(name=name, email=email, role=role, password_hash=hash_password(DEMO_PASSWORD))
        u.districts = [by_name[n] for n in dnames]
        users.append(u)
    db.add_all(users)
    db.flush()
    admin, mod1, mod2, organizer, citizen = users

    now = datetime.now(timezone.utc)
    problems = []
    for i, (title, desc, ci, di, lat, lng, addr, status, prio) in enumerate(PROBLEMS):
        p = Problem(title=title, description=desc, category_id=categories[ci].id, district_id=districts[di].id,
                    author_id=citizen.id, lat=lat, lng=lng, address=addr, status=status, priority=prio,
                    discovered_at=date.today() - timedelta(days=10 - i), created_at=now - timedelta(days=9 - i))
        db.add(p)
        db.flush()
        db.add(ModerationHistory(problem_id=p.id, new_status="pending", comment="Сообщение создано"))
        if status != "pending":
            mod = mod1 if districts[di].name in ("Ленинский", "Первомайский") else mod2
            db.add(ModerationHistory(problem_id=p.id, moderator_id=mod.id, old_status="pending",
                                     new_status="confirmed" if status != "extra_check" else "extra_check",
                                     comment="Проверено по фото и координатам"))
        problems.append(p)

    db.add_all([ProblemSupport(user_id=u.id, problem_id=problems[0].id) for u in (citizen, organizer, mod1)])
    db.add(ProblemSupport(user_id=citizen.id, problem_id=problems[1].id))

    e1 = Event(title="Субботник на Ала-Арче", description="Собираем мусор вдоль русла реки. Перчатки и мешки выдаются.",
               problem_id=problems[0].id, organizer_id=organizer.id, type="volunteer", address=problems[0].address,
               lat=problems[0].lat, lng=problems[0].lng, starts_at=now + timedelta(days=5),
               works=["Сбор мусора", "Сортировка пластика", "Погрузка мешков"], max_participants=30,
               planned_result="Очищено 300 м берега", status="planned")
    e2 = Event(title="Уборка у Ошского рынка", description="Совместная уборка тротуаров и газонов.",
               problem_id=problems[6].id, organizer_id=organizer.id, type="volunteer", address=problems[6].address,
               lat=problems[6].lat, lng=problems[6].lng, starts_at=now - timedelta(hours=2),
               works=["Уборка тротуаров"], max_participants=15, planned_result="Чистая улица", status="in_progress")
    problems[0].status = "planned"
    db.add_all([e1, e2])
    db.flush()
    db.add(EventParticipant(event_id=e1.id, user_id=citizen.id))
    db.add(Subscription(user_id=citizen.id, district_id=districts[0].id))
    db.commit()
    print(f"Готово. Демо-аккаунты (пароль {DEMO_PASSWORD}):")
    for _, email, role, _d in USERS:
        print(f"  {role:10} {email}")


if __name__ == "__main__":
    run(reset="--reset" in sys.argv)
