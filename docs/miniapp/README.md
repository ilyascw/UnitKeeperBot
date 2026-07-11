# Miniapp Delivery Backlog

## Purpose

Этот backlog описывает очередь для главного UX слоя UnitKeeper: Telegram Mini App.

Стек для miniapp зафиксирован:
- `Vite`
- `React`
- `TypeScript`
- `Telegram UI Kit`

Источники:
- `miniapp/PLAN.md`
- `docs/legacy-functionality.md`
- `docs/backend/README.md`
- `docs/layer-delivery-map.md`

## What Blocks Miniapp Today

Основа продукта уже есть в `common` и частично в `backend`, но miniapp пока блокируется следующими пробелами:
- нет task import/history/approval inbox API;
- нет balances/transfers API;
- нет deep link и resilience слоя для bot-driven entry points.

## Queue

`P0`
- [Issue 03](./issue-03-tasks-and-approval-flows.md) Tasks, execution и approval flows
- [Issue 04](./issue-04-balances-progress-and-content.md) Balances, sprint progress и static content

`P1`
- [Issue 05](./issue-05-deep-links-resilience-and-release-hardening.md) Deep links, resilience и release hardening

## Archived

- [Issue 01](../archive/miniapp/issue-01-foundation-and-app-shell.md) Foundation и app shell
- [Issue 02](../archive/miniapp/issue-02-onboarding-and-group-surface.md) Onboarding и group surface

## Notes

- Miniapp не дублирует бизнес-правила backend локально.
- Если экран зависит от неготового backend contract, сначала закрывается backend issue, потом UI.

## Product/design handoff

- [Текущее состояние функционала и экранов](./current-functionality-and-screens.md)
- [ТЗ для дизайнера](./designer-brief.md)
