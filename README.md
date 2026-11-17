# 🌿 EcoSpot

Веб-платформа для поиска и совместного решения местных экологических проблем Бишкека.
Курсовой проект по дисциплине «Процессы проектирования и разработки ПО» (КГТУ им. И. Раззакова, ПИ-2-24).

**Стек:** React + TypeScript + Vite · Leaflet / OpenStreetMap · Python FastAPI · SQLAlchemy · PostgreSQL · JWT

## Статус: этап 1 из 2 (~50 % ТЗ)

| Раздел ТЗ | Статус |
|---|---|
| Архитектура и база данных (все 17 таблиц, в т.ч. финансовые) | ✅ |
| FR-01 Регистрация и вход (JWT, bcrypt) | ✅ (восстановление пароля — этап 2) |
| FR-02/03 Интерактивная карта, выбор района, автоопределение района | ✅ |
| FR-04 Создание проблемы с фото и координатами | ✅ |
| FR-05 Модерация: подтверждение, отклонение с причиной, дубликат, доп. проверка, поиск похожих | ✅ |
| FR-06 Статистика и модераторы по районам | ✅ |
| FR-07/08 Карточка проблемы, поддержка (1 раз на пользователя), комментарии | ✅ |
| FR-09 Уведомления: модераторам, подписчикам района/категории, автору, общие | ✅ (внутренние; e-mail — этап 2) |
| FR-10/11/17/18 Волонтёрские мероприятия: запись, лимит, участие, статусы, отчёт | ✅ |
| FR-19 Поиск и фильтры | ✅ |
| FR-20 Личный кабинет, подписки | ✅ |
| FR-21 Админ-панель: роли, назначение модераторов, рассылка | ⚠️ частично |
| FR-22 Статистика | ⚠️ базовая |
| FR-12–16 Финансируемые мероприятия, смета, сбор средств, платежи, выплаты, отчётность | ⏳ этап 2 (таблицы созданы) |
| Жалобы, журнал действий в UI, e-mail, резервное копирование | ⏳ этап 2 |

## Структура

```
EcoSpot/
├── backend/            FastAPI-приложение
│   ├── app/
│   │   ├── main.py         точка входа, CORS, статика /uploads
│   │   ├── models.py       ORM-модели (раздел 11 ТЗ)
│   │   ├── schemas.py      Pydantic-схемы
│   │   ├── security.py     JWT, хеширование паролей, роли
│   │   ├── notify.py       система уведомлений
│   │   ├── seed.py         создание таблиц + демо-данные
│   │   └── routers/        auth, problems (+модерация), events, notifications, common
│   └── requirements.txt
├── frontend/           React + TypeScript
│   └── src/ pages/, components/, api.ts, auth.tsx
├── db/schema.sql       DDL-схема PostgreSQL (pg_dump)
└── .vscode/            задачи запуска для VS Code
```

## Запуск

Требуется: Python 3.11+, Node.js 18+, PostgreSQL 14+.

**1. База данных** (через psql под суперпользователем):

```sql
CREATE ROLE ecospot LOGIN PASSWORD 'ecospot';
CREATE DATABASE ecospot OWNER ecospot ENCODING 'UTF8' TEMPLATE template0;
```

**2. Backend**

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env          # при необходимости поправьте DATABASE_URL (порт!)
python -m app.seed              # создаёт таблицы и демо-данные
uvicorn app.main:app --reload --port 8000
```

Swagger-документация API: http://127.0.0.1:8000/docs

**3. Frontend**

```bash
cd frontend
npm install
npm run dev
```

Открыть http://localhost:5173

В VS Code: `Terminal → Run Task → Запустить всё`.

## Тестирование

54 автотеста API (pytest) на отдельной базе `ecospot_test`:

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

Тест-кейсы, покрытие требований и критериев приёмки: [docs/testing.md](docs/testing.md). HTML-отчёт: [docs/test-report.html](docs/test-report.html).

## Демо-аккаунты

Пароль у всех: `ecospot123`

| Роль | Почта |
|---|---|
| Администратор | admin@ecospot.kg |
| Модератор (Ленинский, Первомайский) | mod.leninsky@ecospot.kg |
| Модератор (Октябрьский, Свердловский) | mod.oktyabrsky@ecospot.kg |
| Организатор | organizer@ecospot.kg |
| Житель | user@ecospot.kg |

## Статусы

- **Проблема:** pending → (extra_check) → confirmed / rejected / duplicate → planned → in_progress → resolved
- **Мероприятие:** planned → in_progress → completed (или cancelled). Статус мероприятия автоматически меняет статус проблемы.

## Основные эндпоинты REST API

| Метод | Путь | Описание |
|---|---|---|
| POST | /api/auth/register, /api/auth/login | регистрация / вход |
| GET | /api/problems | список с поиском и фильтрами |
| POST | /api/problems | новая проблема (статус «Ожидает проверки») |
| POST | /api/problems/{id}/photos | загрузка фото |
| POST | /api/problems/{id}/support | поддержать / снять поддержку |
| GET | /api/problems/moderation/queue | очередь модератора по его районам |
| POST | /api/problems/{id}/moderate | решение модератора |
| GET/POST | /api/events | мероприятия |
| POST | /api/events/{id}/register, /cancel, /status | запись, отмена, смена статуса |
| GET/PUT | /api/subscriptions | подписки на районы и категории |
| GET | /api/notifications | уведомления |
| GET | /api/stats/districts, /api/stats/summary | статистика |
