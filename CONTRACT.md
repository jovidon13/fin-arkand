# ARKAND Finance — внутренний контракт разработки

Единый свод правил, на который опираются **все** модули backend и frontend. Он выведен из
`docs/design-architecture.txt` (дизайн-система и архитектура) и `docs/part6-finance.txt`
(Часть 6 — Финансы). Любой новый Django-app и FSD-слайс обязан следовать этим правилам.

---

## 0. Термины и коды ТЗ

| Код         | Смысл |
|-------------|-------|
| ФНС-01…04   | Приходы / расходы по статьям / учёт по бизнесу и способу оплаты / прибыль |
| ФНС-10…13   | Отчёты: поступления-расходы, кассы, взаиморасчёты, ФОТ и прибыль |
| КАС-01…04   | Кассы, способ оплаты, лимит оборота, изоляция «своё» |
| БАР-01…04   | Автодолг при передаче, реестр, закрытие, бартер |
| ЗРП-01…05   | Расчёт ЗП, оклады (объектные/адм.), продажники фикс+бонус, примеры схем |
| ХОЛ-20…24   | Лимит расходов на бизнес, порог крупно/мелко, авто-запрос согласия 3 владельцев |
| ХОЛ-30…33   | Автофиксация долга, прозрачный реестр, закрытие, бартер |

Бизнесы холдинга (Часть 0): `Застройщик`, `Проектная компания`, `Бетонный завод`,
`Щебёночный завод`, плюс отделы-сервисы `Снабжение` и `Финансы`.
Владельцы: `Сохиб` (финансы+застройщик), `Ифтихор` (заводы), `Довуд` (проектная).

---

## 1. Backend — общие правила (Django 5 + DRF)

### 1.1 Слои внутри app (строго)
```
models.py       структура данных + инварианты уровня записи. БЕЗ бизнес-логики.
selectors.py    чтение: выборки, фильтры, агрегации. Только read, без записи в БД.
services.py     запись: вся бизнес-логика и транзакции. ТОЛЬКО здесь пишем в БД.
serializers.py  валидация входа + форма ответа. Без доменной логики.
views.py        тонкие ViewSet/APIView: принять → вызвать сервис/селектор → отдать.
permissions.py  RBAC + object-level («своё/чужое»).
filters.py      django-filter FilterSet для списков.
urls.py         router + urlpatterns (см. 1.7).
tests/          pytest-тесты сервисов и API.
```
Бизнес-логика живёт в `services.py`/`selectors.py`. Views и serializers — тонкие.
Сервис можно звать из API, из Celery и из management-команды.

### 1.2 Денежные инварианты — ОБЯЗАТЕЛЬНЫ
- **Только Decimal**: `DecimalField(max_digits=14, decimal_places=2)`. Никогда `float`.
  Хелпер `apps.core.money.money(...)` и `Money = Decimal` quantize к 2 знакам.
- **Атомарность**: любая денежная операция — внутри `@transaction.atomic`. При конкуренции —
  `select_for_update()` на изменяемых денежных записях (кассы, долги).
- **Идемпотентность**: повтор запроса не создаёт вторую операцию. Заголовок
  `Idempotency-Key` → таблица `core.IdempotencyKey`; либо проверка статуса перед переходом.
- **Аудит**: каждое изменение денег/статуса пишется через `AuditLog.record(...)` (кто, что,
  когда, до/после). См. 1.5.
- **Soft-delete**: финансовые записи не удаляются физически — `is_deleted=True` + `deleted_at`.
  Менеджер `objects` скрывает удалённые; `all_objects` — включает.
- **Изоляция касс**: «касса видит только своё» через фильтрацию queryset (`selectors`) +
  object-level permission, а НЕ скрытием в UI.

### 1.3 Базовые модели (`apps/core/models.py`)
- `TimeStampedModel(abstract)` — `created_at`, `updated_at`.
- `SoftDeleteModel(abstract)` — `is_deleted`, `deleted_at`, менеджеры `objects`/`all_objects`,
  метод `soft_delete(actor)`.
- `MoneyBaseModel = TimeStampedModel + SoftDeleteModel` — базовый для денежных сущностей.
- `Business` — бизнес холдинга: `code` (slug enum), `name`, `kind`
  (`developer|design|concrete_plant|crushing_plant|supply|finance`), `is_active`.
- `City`, `SiteObject` — сквозное измерение «объект/город» (ХОЛ-06); опционально на транзакциях.
- `IdempotencyKey` — `key`, `scope`, `response_hash`, `created_at`.

### 1.4 Enums (`TextChoices`) — общий словарь
- `TxKind`: `income`, `expense`.
- `PayMethod`: `cash`, `transfer`.
- `TxStatus`: `draft`, `pending`, `confirmed`, `rejected`, `void`.
- `ExpenseCategory` — модель-справочник (материалы, зарплата, налоги, электроэнергия,
  ремонт техники, транспорт, прочее) с `code`, `name`, `is_active`.
- `DebtStatus`: `open`, `partially_settled`, `settled`.
- `SettlementKind`: `netting` (взаимозачёт), `repayment` (возврат), `barter` (бартер).
- `ApprovalStatus`: `pending`, `approved`, `rejected`.
- `PayrollStatus`: `draft`, `calculated`, `approved`, `paid`.
- `EmployeeSalaryType`: `object` (объектный), `admin` (административный).

### 1.5 Аудит (`apps/audit`)
```python
AuditLog.record(actor, action: str, target, *, before=None, after=None, meta=None)
```
`action` — dotted string, напр. `transfer.approved`, `tx.confirmed`, `debt.settled`,
`payroll.run`, `cash.limit.changed`. `target` — любая модель (GenericForeignKey).
Всё, что меняет деньги/статусы, вызывает `record` внутри той же транзакции.

### 1.6 API-конвенции
- Версия: префикс `/api/v1/`.
- Auth: JWT (SimpleJWT) — `Authorization: Bearer <access>`. `/api/v1/auth/token`,
  `/api/v1/auth/token/refresh`, `/api/v1/auth/me`.
- Списки: пагинация (`PageNumberPagination`, `page`, `page_size`) + фильтры (django-filter)
  + сортировка (`ordering`).
- **Деньги в JSON — строка**, не float. DRF `DecimalField(coerce_to_string=True)` (дефолт).
- Единый формат ошибки: `{ "code": "<slug>", "message": "<human>", "details": {...} }`.
  Реализуется через `apps.core.exceptions.custom_exception_handler` +
  доменные исключения `DomainError(code, message, details)`.
- Именование роутов: kebab/lower, множественное число — `transactions`, `cash-registers`,
  `debts`, `transfers`, `settlements`, `employees`, `payroll-runs`, `approval-requests`.

### 1.7 Регистрация URL (важно для сборки)
Каждый app экспортирует в `<app>/urls.py`:
```python
router = DefaultRouter()
router.register("transactions", TransactionViewSet, basename="transaction")
urlpatterns = router.urls   # + доп. пути при необходимости
```
`config/urls.py` подключает: `path("api/v1/", include("apps.<app>.urls"))`.
Basename и префикс роута фиксированы в разделе 3.

### 1.8 Permissions / роли (RBAC)
Роли (`accounts.Role.code`): `owner`, `chief_accountant`, `accountant`, `cashier`,
`admin`. Плюс `is_owner` через связь с `Business`-зоной.
- `owner` — видит всё, согласует крупные расходы.
- `chief_accountant` — все финоперации + важные.
- `accountant` — приходы/расходы, взаиморасчёты, бартер, зарплата.
- `cashier` — только своя касса (object-level), в пределах лимита.
- `admin` — администрирование, роли/права/лимиты.

Базовые классы в `apps/accounts/permissions.py`: `IsAuthenticatedRole`, `HasRole("...")`,
`IsOwner`, `CashRegisterScoped` (object-level для касс). Домены импортируют их.

### 1.9 Тесты
`pytest` + `pytest-django` + `factory_boy`. Файлы `apps/<app>/tests/test_*.py`.
Обязательно покрыть: автодолг при одобренной передаче (БАР-01), лимит кассы (КАС-03),
расчёт зарплаты по гибкой схеме (ЗРП-03…05), порог согласования (ХОЛ-21…23),
идемпотентность подтверждения прихода (ФНС-01).

---

## 2. Frontend — общие правила (React 19 + TS + Vite + FSD)

### 2.1 Слои FSD (импорт строго сверху вниз)
`app → pages → widgets → features → entities → shared`. Слайсы одного слоя не импортируют
друг друга напрямую. Публичный контракт слайса — `index.ts`.

```
src/
├── app/       провайдеры, роутер, тема, i18n, ProtectedRoute, layout
├── pages/     finance, cash, settlements, payroll, reports, login, dashboard
├── widgets/   sidebar, topbar, tx-table, cash-card, debt-registry, ...
├── features/  add-income, add-expense, confirm-tx, close-debt, payroll-run, approve-request
├── entities/  transaction, cash-register, debt, transfer, employee, payroll, business, approval
└── shared/    ui, api, lib, config (tokens.css), i18n
```

### 2.2 Дизайн-токены — единственный источник цвета (`shared/config/tokens.css`)
Хардкод hex в компонентах ЗАПРЕЩЁН. Только переменные:
```
--brand:#A4161A; --brand-hover:#85111A; --brand-deep:#6B0F18;
--ink:#1A1416; --paper:#FAF9F8; --white:#FFFFFF;
--n-50..--n-900 (warm gray);
--success:#15803D; --warning:#B45309; --error:#DC2626; --info:#1D4ED8;
--money-in:#15803D; --money-out:#DC2626; --money-zero:#1A1416;
```
Правила: вишнёвый — только кнопки/навигация/акценты (не деньги/не фон). Деньги —
отдельная семантика: приход зелёный, расход `#DC2626`, ноль тёмный. Серые — тёплые.
Категориальная палитра графиков: Крас/Бирюза/Янтарь/Сланец/Слива/Зелень.

### 2.3 Данные
- `shared/api/client.ts` — Axios instance: baseURL `/api/v1`, интерцептор JWT (access в
  памяти + refresh), единая обработка ошибок `{code,message,details}`.
- TanStack Query для запросов/кэша/инвалидации — хуки живут в `entities/*/api`.
- Zod — валидация ответов API и форм. Схемы в `entities/*/model`.
- Деньги приходят строкой → парсить через `shared/lib/money.ts` (`parseMoney`,
  `formatMoney`, `signColor`). Отрицательные/расход — красный, приход — зелёный.

### 2.4 i18n
`i18next`, языки `ru` (дефолт) и `tj`. Ключи в `shared/i18n/{ru,tj}.json`. Тексты
интерфейса — только через `t("...")`, без строк в JSX.

### 2.5 UI-kit (`shared/ui`)
`Button`, `Input`, `Select`, `Table`, `Badge`, `Card`, `Money` (цвет по знаку),
`StatusBadge`, `Modal`, `PageHeader`, `Toast`. Стили — через токены.

---

## 3. Реестр API-контрактов (фиксирован — не менять именование)

| Модуль      | Роут (под `/api/v1/`) | Основные сущности |
|-------------|-----------------------|-------------------|
| accounts    | `auth/*`, `users`, `roles` | User, Role |
| core        | `businesses`, `cities`, `site-objects`, `expense-categories` | Business, City, SiteObject, ExpenseCategory |
| finance     | `transactions` | Transaction |
| cash        | `cash-registers`, `cash-operations` | CashRegister, CashOperation |
| settlements | `transfers`, `debts`, `settlements` | Transfer, Debt, Settlement |
| payroll     | `employees`, `payroll-runs`, `payroll-schemes` | Employee, PayrollRun, PayrollItem, PayrollScheme |
| approvals   | `approval-requests` | ApprovalRequest, ApprovalVote |
| reports     | `reports/pnl`, `reports/cash`, `reports/settlements`, `reports/payroll` | (read-only агрегаты) |
| audit       | `audit-logs` (read-only) | AuditLog |

Все денежные суммы в ответах — строки. Все списки — пагинированы и фильтруемы.

---

## 4. Ключевые бизнес-правила (реализовать точно)

1. **ФНС-01 приход**: создаётся в статусе `pending`; подтверждение финансистом →
   `confirmed`, пишется в кассу/баланс, аудит. Идемпотентно.
2. **КАС-03 лимит оборота**: у кассы `turnover_limit`. Операция, превышающая оборот за
   период, блокируется (`DomainError("cash_limit_exceeded")`). Факт = остаток в системе.
3. **КАС-04 изоляция**: кассир видит и меняет только свою кассу; финотдел/владельцы — все.
4. **БАР-01 / ХОЛ-30 автодолг**: при `approve_transfer` создаётся `Debt`
   (debtor=получатель, creditor=отправитель, amount) в той же транзакции + аудит.
5. **БАР-03 закрытие**: `settle_debt` (netting/repayment) уменьшает `outstanding`;
   статус → `partially_settled`/`settled`. Взаимозачёт ищет встречный долг.
6. **ХОЛ-20…24 согласование**: у бизнеса `expense_limit`. Расход/закупка выше порога →
   `ApprovalRequest` с 3 голосами владельцев; проводится только при 3 `approved`,
   иначе ждёт; в пределах лимита — без запроса.
7. **ЗРП-03…05 зарплата**: `PayrollScheme` — гибкая (fixed + rules). Пример завод:
   `fix 3000 + 10% от продаж`; застройщик: `fix 3000 + 500/кв, при >10 кв/мес → 1000/кв`.
   `run_payroll(period)` считает `PayrollItem` по каждому сотруднику.
8. **Прибыль ФНС-04**: `income − expense` по бизнесу за период (selectors, агрегаты).

Держись этого документа. Если правило ТЗ конфликтует с удобством — выигрывает ТЗ.
