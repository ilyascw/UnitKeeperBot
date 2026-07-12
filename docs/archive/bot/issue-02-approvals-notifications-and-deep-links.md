# Issue 02: Approvals, Notifications, And Deep Links

**Status:** Closed and archived

## Priority

`P1`

## Why

Approval/rejection и точечные user notifications остаются естественной задачей для Telegram bot, но только если сам bot не вычисляет эти события.

## Goal

Сделать bot delivery-слоем для approval notifications и deep-link entry points в miniapp.

## Scope

- [x] Получение pending notification events из backend outbox.
- [x] Отправка approval/rejection сообщений участникам.
- [x] Inline approve/reject actions через backend internal endpoints.
- [x] Deep links в:
  - approval inbox;
  - task detail/history;
  - relevant miniapp screen по notification type.
- [x] Delivery ack/fail cycle.

## Acceptance Criteria

- [x] bot получает события из backend, а не вычисляет pending approvals сам;
- [x] approve/reject flow не ходит в БД напрямую;
- [x] пользователь из уведомления попадает в точный miniapp screen;
- [x] delivery ошибки не приводят к silent loss событий.

## Dependencies

- После `docs/archive/backend/issue-04-task-approval-inbox-and-log-query-api.md`.
- После `docs/backend/issue-07-notification-outbox-and-deep-links.md`.
- После `docs/archive/common/issue-02-outbox-and-idempotency-schema.md`.

## Legacy References

- `UnitKeeperBot/handlers/tasks.py`
