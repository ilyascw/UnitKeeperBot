# Issue 09: Admin Ops And Legacy Cutover

## Priority

`P2`

## Why

После того как miniapp и thin bot смогут жить на backend, останутся финальные хвосты миграции:
- admin-like `kill_tasks`;
- fallback сценарии бота;
- удаление ORM-логики из legacy handlers;
- финальная сверка поведения.

## Goal

Закрыть остатки legacy-зависимости и подготовить выключение старой бизнес-логики в боте.

## Scope

- Решить судьбу `kill_tasks`:
  - backend admin endpoint;
  - cron/admin tool;
  - либо явное удаление из продукта.
- Проверить, что bot handlers больше не читают/пишут бизнес-данные напрямую.
- Перевести все пользовательские действия на backend contracts.
- Составить cutover checklist:
  - feature parity;
  - migrations applied;
  - env configured;
  - bot switched to internal backend transport.

## Acceptance Criteria

- legacy bot не содержит бизнес-решений, кроме UI/notification routing;
- есть documented cutover plan;
- можно отключить старые handler-ORM сценарии без потери функций.

## Dependencies

- После Issues 01-08.

## Legacy References

- `UnitKeeperBot/handlers`
- `UnitKeeperBot/sprint_results.py`

## Existing Backend References

- `docs/legacy-functionality.md`
- `backend/PLAN.md`
