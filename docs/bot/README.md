# Bot Delivery Backlog

## Purpose

Этот backlog фиксирует, как довести `bot` до thin-bot модели.

Источники:
- `bot/PLAN.md`
- `docs/legacy-functionality.md`
- `docs/backend/README.md`
- `docs/layer-delivery-map.md`

## What Bot Should Become

Целевое состояние:
- `/start`, `/help`, `/about` и fallback-команды;
- approval notifications и inline review actions;
- sprint reports и reminders;
- deep links в miniapp;
- никакой самостоятельной бизнес-логики и прямой ORM-работы.

## Queue

`P0`
- [Issue 01](./issue-01-thin-bot-shell-and-backend-transport.md) Thin bot shell и backend transport

`P1`
- [Issue 02](./issue-02-approvals-notifications-and-deep-links.md) Approval notifications и deep links
- [Issue 03](./issue-03-reports-reminders-and-fallback-ops.md) Reports, reminders и fallback ops

## Notes

- Если flow можно чисто решить через miniapp + backend, bot не должен возвращать себе старый FSM UX.
