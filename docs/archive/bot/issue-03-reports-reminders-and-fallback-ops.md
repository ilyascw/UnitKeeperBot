# Issue 03: Reports, Reminders, And Fallback Ops

**Status:** Closed and archived

## Priority

`P1`

## Why

После approval notifications боту остаются ещё три важных обязанности:
- доставлять sprint reports;
- отправлять reminders;
- держать минимальные recovery/admin сценарии на случай недоступности miniapp.

## Goal

Закрыть все bot-only обязанности без возврата к legacy business logic.

## Scope

- [x] Доставка personal sprint reports и owner summary.
- [x] Reminders:
  - pending approvals;
  - sprint deadline;
  - critical membership/group events.
- [x] Minimal fallback/recovery flows, если часть miniapp временно недоступна.
- [x] Решение по admin-like операциям: recovery не возвращает business flows в bot.

## Acceptance Criteria

- [x] bot отправляет sprint summaries на событиях/данных из backend;
- [x] reminders формируются не внутри handlers, а на backend-owned job/outbox layer;
- [x] минимальные recovery actions задокументированы и не расползаются в полноценный старый UX.

## Dependencies

- После `docs/backend/issue-06-sprint-close-jobs-and-scheduler.md`.
- После `docs/backend/issue-07-notification-outbox-and-deep-links.md`.
- После `docs/backend/issue-08-reminders-idempotency-observability-and-tests.md`.
- Синхронизировать с `docs/backend/issue-09-admin-ops-and-legacy-cutover.md`.

## Legacy References

- `UnitKeeperBot/sprint_results.py`
- `UnitKeeperBot/handlers/tasks.py`
