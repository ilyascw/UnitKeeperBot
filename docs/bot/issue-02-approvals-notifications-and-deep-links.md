# Issue 02: Approvals, Notifications, And Deep Links

## Priority

`P1`

## Why

Approval/rejection и точечные user notifications остаются естественной задачей для Telegram bot, но только если сам bot не вычисляет эти события.

## Goal

Сделать bot delivery-слоем для approval notifications и deep-link entry points в miniapp.

## Scope

- Получение pending notification events из backend outbox.
- Отправка approval/rejection сообщений участникам.
- Inline approve/reject actions через backend internal endpoints.
- Deep links в:
  - approval inbox;
  - task detail/history;
  - relevant miniapp screen по notification type.
- Delivery ack/fail cycle.

## Acceptance Criteria

- bot получает события из backend, а не вычисляет pending approvals сам;
- approve/reject flow не ходит в БД напрямую;
- пользователь из уведомления попадает в точный miniapp screen;
- delivery ошибки не приводят к silent loss событий.

## Dependencies

- После `docs/backend/issue-04-task-approval-inbox-and-log-query-api.md`.
- После `docs/backend/issue-07-notification-outbox-and-deep-links.md`.
- После `docs/common/issue-02-outbox-and-idempotency-schema.md`.

## Legacy References

- `UnitKeeperBot/handlers/tasks.py`
