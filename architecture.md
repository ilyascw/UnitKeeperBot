# UnitKeeper Architecture

## Контекст системы

UnitKeeper состоит из четырёх независимо запускаемых компонентов:

1. `miniapp` — ежедневный интерфейс внутри Telegram WebView;
2. `backend` — единственный владелец бизнес-правил и HTTP-контрактов;
3. `bot` — transport для команд, уведомлений и deep links;
4. `common` — схема данных, миграции и общая persistence-модель.

```mermaid
C4Context
    title UnitKeeper system context
    Person(user, "Участник группы", "Планирует и подтверждает повторяющиеся задачи")
    System_Ext(telegram, "Telegram", "Mini Apps runtime и Bot API")
    System(unitkeeper, "UnitKeeper", "Спринты, задачи, approvals и баланс нагрузки")
    SystemDb(postgres, "PostgreSQL", "Состояние продукта, ledger, outbox")

    Rel(user, telegram, "Работает через")
    Rel(telegram, unitkeeper, "initData, updates, Bot API")
    Rel(unitkeeper, postgres, "SQLAlchemy / Alembic")
```

## Контейнеры и потоки данных

```mermaid
sequenceDiagram
    actor User as Пользователь
    participant UI as Mini App
    participant API as FastAPI
    participant DB as PostgreSQL
    participant Job as Scheduler
    participant Bot as aiogram bot

    User->>UI: Открывает приложение
    UI->>API: POST /auth/telegram (signed initData)
    API->>API: Проверка HMAC и выпуск сессии
    API-->>UI: Access token + current context

    User->>UI: Отмечает задачу выполненной
    UI->>API: POST /tasks/{id}/done
    API->>DB: Task log + outbox event в одной транзакции
    Bot->>API: Claim pending notification
    Bot->>User: Approval request
    Bot->>API: Ack / fail delivery

    Job->>API: Application service: close due sprint
    API->>DB: Sprint result + zero-sum ledger + reports
```

## Backend

Backend разделён по направлению зависимостей:

```text
api/                 FastAPI routers, auth dependencies, Pydantic schemas
application/         use cases, ports, orchestration и jobs
domain/              ошибки и чистая sprint math
infrastructure/      SQLAlchemy repositories, UoW, auth, clock
entrypoints/         API и отдельный scheduler process
```

FastAPI router не содержит SQL и расчётов. Application service работает с
портами и Unit of Work; конкретные SQLAlchemy-репозитории подключаются через
Dishka.

## Data model

Основные агрегаты:

- `groups`, `group_memberships`, `group_member_weights`;
- `tasks`, `task_logs`;
- `sprint_runs`, `sprint_member_results`;
- `balances`, `balance_transactions`;
- `notification_outbox_events`, `notification_delivery_attempts`;
- `idempotency_keys`.

`balances.current_balance` — быстрый read model. Аудируемым источником изменений
служит append-only `balance_transactions`. Логическая операция объединяет
проводки через `transaction_group_id`; сумма `amount_delta` в группе должна
равняться нулю.

## Надёжность и безопасность

- Telegram `initData` проверяется на backend по токену бота и TTL.
- Bot использует отдельный internal transport с shared secret.
- Scheduler запускается отдельным процессом; duplicate protection хранится в БД.
- Outbox отделяет фиксацию бизнес-события от нестабильного Telegram API.
- Ошибки доставки подтверждаются через `ack`/`fail`, retries не теряют исходное
  событие и correlation ID.
- Alembic smoke test проверяет полное развёртывание схемы с нуля.

## Известные компромиссы

- Групповой join code пока хранится как прикладной secret, а не как отдельная
  invitation entity.
- Планировщик использует UTC, timezone группы ещё не влияет на cron.
- Ledger имеет структурные ограничения на отдельные проводки; периодическая
  reconciliation-проверка read model пока не реализована.
