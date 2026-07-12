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

Активных bot issues нет. Issues 01-03 реализованы и находятся в
[`docs/archive/bot`](../archive/bot/).

## Notes

- Если flow можно чисто решить через miniapp + backend, bot не должен возвращать себе старый FSM UX.
