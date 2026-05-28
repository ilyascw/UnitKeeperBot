# Issue 08: Reminders, Idempotency, Observability, And Tests

## Priority

`P1`

## Why

Даже после добавления основного API backend останется хрупким без:
- reminder jobs;
- idempotency;
- полноценного test matrix;
- structured logging и request tracing.

Это критично для production-minded сервиса и прямо следует из `backend/PLAN.md`.

## Goal

Добрать reliability слой, необходимый до реального подключения miniapp и bot в production-like режиме.

## Scope

- Reminder jobs:
  - pending approvals;
  - sprint deadline reminders.
- Idempotency strategy:
  - repeated Telegram callbacks;
  - repeated bot delivery attempts;
  - repeated client retries на write endpoints.
- Observability:
  - request id;
  - job logs;
  - structured service logs.
- Tests:
  - unit tests for weights and sprint math;
  - API contract tests;
  - repository / DB integration tests;
  - transfer and notification flow tests.

## Acceptance Criteria

- повторная доставка одного и того же action не ломает состояние;
- есть request/job correlation ids;
- coverage закрывает критические use cases;
- reminder logic не сидит в bot handlers;
- backend можно дебажить по логам без ручного SQL.

## Dependencies

- После Issue 06 и Issue 07.

## Legacy References

- `UnitKeeperBot/handlers/tasks.py`
- `UnitKeeperBot/sprint_results.py`

## Existing Backend References

- `backend/tests/unit`
- `backend/PLAN.md`
