# Деплой ARKAND Finance

Монорепозиторий, две независимо деплоящиеся части:

| Часть      | Каталог     | Платформа | Что это                                  |
| ---------- | ----------- | --------- | ---------------------------------------- |
| Backend    | `backend/`  | Railway   | Django + DRF API + PostgreSQL            |
| Frontend   | `frontend/` | Vercel    | React SPA (Vite), статика                |

Порядок: **сначала бэкенд на Railway** (получишь URL API), **потом фронтенд на
Vercel** (пропишешь этот URL). Затем вернёшься в Railway и добавишь домен
Vercel в CORS.

> Разбивать репозиторий на два **не нужно** — обе платформы умеют собирать
> подкаталог монорепо через настройку **Root Directory**.

---

## 1. Backend → Railway

### 1.1 Создать проект и базу
1. [railway.com](https://railway.com) → **New Project** → **Deploy from GitHub repo** → выбери `arkand-finance`.
2. В сервисе: **Settings → Root Directory** = `backend`.
   Railway найдёт `backend/Dockerfile` и `backend/railway.json` и соберёт образ.
3. В проект добавь БД: **New → Database → Add PostgreSQL**.

### 1.2 Переменные окружения сервиса
**Settings → Variables** у backend-сервиса:

| Переменная               | Значение                                                        |
| ------------------------ | --------------------------------------------------------------- |
| `DJANGO_SECRET_KEY`      | длинная случайная строка (см. ниже)                             |
| `DJANGO_DEBUG`           | `0`                                                             |
| `DATABASE_URL`           | `${{Postgres.DATABASE_URL}}` — ссылка на плагин Postgres         |
| `DJANGO_SETTINGS_MODULE` | `config.settings.prod` (уже задан в Dockerfile; можно не дублировать) |
| `CORS_ALLOWED_ORIGINS`   | URL фронта на Vercel, напр. `https://arkand-finance.vercel.app` |
| `SEED_DEMO`              | `1` — только на ПЕРВЫЙ деплой, чтобы залить демо-данные, потом `0` |

Секретный ключ:
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Публичный домен Railway (`RAILWAY_PUBLIC_DOMAIN`) подставляется автоматически в
`ALLOWED_HOSTS` и `CSRF_TRUSTED_ORIGINS` (см. `config/settings/prod.py`) — руками
хост прописывать не надо.

### 1.3 Домен и запуск
1. **Settings → Networking → Generate Domain** — получишь `https://<...>.up.railway.app`.
2. Railway соберёт и задеплоит. На старте контейнер (см. `entrypoint.sh`):
   ждёт БД → `migrate` → `collectstatic` → (если `SEED_DEMO=1`) `seed_demo` →
   запускает gunicorn на `$PORT`.
3. Проверь: `https://<backend>.up.railway.app/healthz` → `{"status":"ok"}`.
   API-доки: `/api/v1/docs/`, админка: `/admin/`.

Демо-логины (если сидил): владельцы `sohib` / `iftikhor` / `dovud`, гл.бухгалтер
`chief`, бухгалтеры `buh1`/`buh2`, кассиры `cashier_dev`/`cashier_des`, `admin`.
Пароль у всех — `arkand2026`. **Смени пароли/отключи сид на проде.**

---

## 2. Frontend → Vercel

### 2.1 Импорт проекта
1. [vercel.com](https://vercel.com) → **Add New → Project** → импортируй `arkand-finance`.
2. **Root Directory** = `frontend`. Framework определится как **Vite**
   (`frontend/vercel.json` уже задаёт build/output/SPA-rewrite).

### 2.2 Переменная окружения
**Settings → Environment Variables** (scope: Production + Preview):

| Переменная     | Значение                                                |
| -------------- | ------------------------------------------------------- |
| `VITE_API_URL` | `https://<backend>.up.railway.app/api/v1` (с `/api/v1`!) |

> Vite «вшивает» `VITE_*` на этапе сборки — после изменения переменной нужен
> **Redeploy**.

### 2.3 Деплой
**Deploy**. Получишь `https://arkand-finance.vercel.app`. Роутинг SPA (обновление
страницы на любом маршруте) работает благодаря rewrite на `index.html`.

---

## 3. Связать их (CORS)

После того как узнал домен Vercel, вернись в Railway → Variables и убедись, что:

```
CORS_ALLOWED_ORIGINS=https://arkand-finance.vercel.app
```

Хочешь, чтобы preview-деплои Vercel тоже ходили в API — добавь:

```
CORS_ALLOWED_ORIGIN_REGEXES=^https://.*\.vercel\.app$
```

Railway передеплоит сам. Открой фронт, залогинься — сетевых/CORS-ошибок быть не должно.

---

## 4. Чек-лист

- [ ] `GET /healthz` на Railway отдаёт 200.
- [ ] `/admin/` открывается со стилями (WhiteNoise раздаёт статику).
- [ ] Фронт на Vercel грузится, `/login` работает после F5.
- [ ] Логин проходит, дашборд тянет данные (значит CORS + `VITE_API_URL` верны).
- [ ] `SEED_DEMO` переключён в `0` после первого деплоя.
- [ ] `DJANGO_SECRET_KEY` — уникальный, `DJANGO_DEBUG=0`.

## 5. Частые проблемы

| Симптом                                   | Причина / решение                                                       |
| ----------------------------------------- | ----------------------------------------------------------------------- |
| CORS-ошибка в консоли браузера            | `CORS_ALLOWED_ORIGINS` не совпадает с доменом Vercel (проверь `https://`, без слэша в конце) |
| Фронт стучится на `localhost:8000`        | Не задан `VITE_API_URL` на Vercel, либо не сделан Redeploy после его добавления |
| `DisallowedHost` в логах Railway          | Задай `DJANGO_ALLOWED_HOSTS` или оставь дефолт `*` (домен Railway трастится автоматически) |
| Админка без стилей                        | Не отработал `collectstatic` — смотри логи билда; WhiteNoise должен быть в MIDDLEWARE |
| 404 при F5 на маршруте SPA                | Проверь, что `frontend/vercel.json` с rewrite задеплоился                |
| 502/health check fails на Railway         | Приложение не забиндилось на `$PORT` — не переопределяй CMD/Start Command вручную |

---

Локальный запуск всего стека одной командой — см. `README.md` (`docker compose up`).
