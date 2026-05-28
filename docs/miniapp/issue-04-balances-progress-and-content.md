# Issue 04: Balances, Progress, And Content

## Priority

`P0`

## Why

После onboarding и task UX miniapp должен закрыть ещё три заметных пользовательских поверхности:
- balance;
- sprint progress;
- product/help content, чтобы бот не оставался главным местом объяснений.

## Goal

Дать пользователю в miniapp всё, что нужно для просмотра прогресса, балансов и базового понимания продукта.

## Scope

- Balance screen:
  - current balance;
  - transfer flow;
  - recipient picker;
  - transfer history placeholder или first slice, если backend будет готов.
- Sprint progress screen:
  - plan vs fact;
  - completed task breakdown;
  - progress visualization.
- Content surface для `/about` и, при необходимости, `/help`-материалов.

## Acceptance Criteria

- balance и transfer flow живут в miniapp, а не в legacy bot;
- temp results screen покрывает intent legacy `/temp_results`;
- product explanation доступно в miniapp без обязательного бот-фоллбэка.

## Dependencies

- После `docs/backend/issue-05-balances-and-unit-transfers.md`.
- Опирается на уже существующий sprint results API.

## Legacy References

- `UnitKeeperBot/handlers/balance.py`
- `UnitKeeperBot/handlers/temp_results.py`
- `UnitKeeperBot/handlers/about.py`
- `UnitKeeperBot/handlers/help.py`
