# ARKAND — Финансовая CRM холдинга

Единая финансовая CRM-система холдинга (застройка, проектирование, бетонный и щебёночный
заводы + общие отделы). Реализует **Часть 6 — Финансы** и опорную **Часть 0 — Архитектура
холдинга** по техническому заданию, строго в соответствии с дизайн-системой и архитектурой
ARKAND.

Backend — модульный монолит **Django 5 + DRF + PostgreSQL**; admin-панель — **React 19 +
TypeScript + Vite** по методологии **Feature-Sliced Design**. Интерфейс двуязычный
(**ru / tj**) с первого дня.

---

## Что умеет система

| Модуль | Коды ТЗ | Возможности |
|--------|---------|-------------|
| **Финансы** | ФНС-01…04 | Приходы с подтверждением финансистом, расходы по статьям, учёт по бизнесу и способу оплаты (наличные/перевод), прибыль по бизнесу за период |
| **Кассы** | КАС-01…04 | Кассы бизнесов, лимит оборота, изоляция «касса видит только своё», факт = остаток в системе |
| **Взаиморасчёты** | БАР-01…04 / ХОЛ-30…33 | Автофиксация долга при одобренной передаче, прозрачный реестр «кто кому должен», закрытие взаимозачётом/возвратом, бартер под контролем бухгалтера |
| **Зарплата** | ЗРП-01…05 | Расчёт в системе, оклады (объектные/административные), гибкие бонусные схемы продажников (фикс + %, за квартиру с порогом) |
| **Согласования** | ХОЛ-20…24 | Лимит расходов на бизнес, порог «крупно/мелко», авто-запрос согласия у всех трёх владельцев, цифровое одобрение |
| **Отчёты** | ФНС-10…13 | Поступления/расходы по бизнесам и сводно, остатки/обороты касс, взаиморасчёты, зарплатный фонд, прибыль по холдингу |
| **Аудит** | — | Журнал всех денежных и статусных изменений (кто, что, когда, до/после) |

### Денежные инварианты (обязательны)
- **Только `Decimal`** для денег (`DecimalField(14,2)`), в JSON — строка, никогда не float.
- **Атомарность**: каждая денежная операция в `transaction.atomic` + `select_for_update`.
- **Идемпотентность**: повтор запроса не создаёт вторую операцию.
- **Аудит**: любое изменение денег/статуса пишется в журнал.
- **Soft-delete**: финансовые записи не удаляются физически.
- **Изоляция касс**: фильтрацией queryset + object-level permission, а не скрытием в UI.

---

## Технологический стек

| Слой | Технологии |
|------|-----------|
| Backend | Python 3.12 · Django 5 · Django REST Framework |
| БД | PostgreSQL 16 |
| Фоновые задачи | Celery + Redis |
| Аутентификация | JWT (SimpleJWT), RBAC |
| Frontend | React 19 · TypeScript · Vite · Feature-Sliced Design |
| Данные UI | TanStack Query · Axios · Zod |
| Локализация | i18next (ru / tj) |
| Инфраструктура | Docker · Nginx |

---

## Структура репозитория

```
arkand-finance/
├── backend/                # Django 5 + DRF (модульный монолит)
│   ├── config/             # settings (base/dev/prod/test), urls, celery, wsgi/asgi
│   └── apps/
│       ├── core/           # Business, справочники, базовые модели, деньги (Часть 0)
│       ├── accounts/       # пользователи, роли, JWT, RBAC
│       ├── finance/        # приходы/расходы, прибыль (ФНС-01…04)
│       ├── cash/           # кассы, лимиты, изоляция (КАС-01…04)
│       ├── settlements/    # взаиморасчёты, долги, бартер (БАР / ХОЛ-30…33)
│       ├── payroll/        # зарплата, гибкие бонусы (ЗРП-01…05)
│       ├── approvals/      # лимиты и согласование расходов (ХОЛ-20…24)
│       ├── reports/        # сводные отчёты (ФНС-10…13)
│       └── audit/          # журнал всех действий
├── frontend/               # React 19 + FSD admin-панель
│   └── src/
│       ├── app/            # провайдеры, роутер, тема, i18n, layout
│       ├── pages/          # finance, cash, settlements, payroll, approvals, reports, …
│       ├── widgets/        # sidebar, topbar, period-filter
│       ├── features/       # add-income, confirm-tx, close-debt, run-payroll, …
│       ├── entities/       # transaction, cash, debt, employee, business, report, …
│       └── shared/         # ui, api, lib, config (tokens.css), i18n
├── docs/                   # исходные ТЗ (PDF) + извлечённый текст
├── CONTRACT.md             # внутренний контракт разработки (конвенции)
├── docker-compose.yml
└── Makefile
```

Слои backend внутри app: `models` → `selectors` (чтение) → `services` (запись/транзакции) →
`serializers` → `views` (тонкие) → `permissions` → `filters` → `urls`. Бизнес-логика живёт в
`services`/`selectors`. Подробности — в [CONTRACT.md](CONTRACT.md).

---

## Быстрый старт — Docker

```bash
cp .env.example .env            # при желании поменяйте секреты
docker compose up -d --build
```

- Admin-панель: **http://localhost:8080**
- API: **http://localhost:8080/api/v1/** · Swagger: **/api/v1/docs/**
- Django admin: **http://localhost:8080/admin/**

Демо-данные засеиваются автоматически (`SEED_DEMO=1`).

---

## Локальная разработка

### Backend
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env

# без Postgres — на sqlite (для проверок и тестов):
export USE_SQLITE=1
python manage.py migrate
python manage.py seed_demo
python manage.py runserver          # http://localhost:8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev                          # http://localhost:5173 (проксирует /api → :8000)
```

---

## Демо-учётные записи

После `seed_demo` доступны (пароль у всех: **`arkand2026`**):

| Логин | Роль |
|-------|------|
| `admin` | Администратор (superuser) |
| `sohib` | Владелец — финансы/застройщик |
| `iftikhor` | Владелец — заводы |
| `dovud` | Владелец — проектная |
| `chief` | Главный бухгалтер |
| `buh1`, `buh2` | Бухгалтеры |
| `cashier_dev`, `cashier_des` | Кассиры (видят только свою кассу) |

---

## API

Все эндпоинты под `/api/v1/`. Аутентификация — JWT:

```
POST /api/v1/auth/token            { username, password } → { access, refresh, user }
POST /api/v1/auth/token/refresh    { refresh } → { access }
GET  /api/v1/auth/me
```

Основные ресурсы: `transactions`, `cash-registers`, `cash-operations`, `transfers`, `debts`,
`settlements`, `employees`, `payroll-runs`, `approval-requests`, `businesses`,
`expense-categories`, `audit-logs`, а также отчёты `reports/pnl|cash|settlements|payroll|dashboard`.

- Списки: пагинация (`page`, `page_size`) + фильтры (`django-filter`) + сортировка (`ordering`).
- Ошибки: единый формат `{ code, message, details }`.
- Деньги в JSON — строка.

Полная схема: `/api/v1/schema/` (OpenAPI) и `/api/v1/docs/` (Swagger UI).

---

## Тесты и качество

```bash
cd backend && USE_SQLITE=1 python -m pytest -q     # доменные тесты бизнес-логики
cd backend && ruff check apps/                     # линт backend
cd frontend && npm run typecheck                   # строгая типизация frontend
cd frontend && npm run build                       # production-сборка
```

Тесты покрывают ключевые правила ТЗ: идемпотентность подтверждения прихода (ФНС-01),
лимит кассы (КАС-03) и изоляцию (КАС-04), автодолг при передаче (БАР-01/ХОЛ-30) и
закрытие/взаимозачёт (БАР-03), гибкие схемы зарплаты (ЗРП-04/05), порог и согласие трёх
владельцев (ХОЛ-22…24), консолидацию прибыли (ФНС-10).

---

## Дизайн-система

Единый визуальный стандарт из логотипа: вишнёвый **Arkand Crimson `#A4161A`** (только кнопки,
навигация, акценты), тёплые нейтральные серые, отдельная семантика денег (приход — зелёный
`#15803D`, расход — сигнальный красный `#DC2626`). Все цвета — только через CSS-переменные из
`frontend/src/shared/config/tokens.css`; хардкод hex в компонентах запрещён.

---

*Исполнитель: WeBrand · Проект: Единая CRM-экосистема холдинга ARKAND.*
