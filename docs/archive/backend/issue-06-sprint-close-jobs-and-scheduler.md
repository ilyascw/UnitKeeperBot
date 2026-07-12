# Issue 06: Sprint Close Jobs And Scheduler

**Status:** Closed and archived

## Priority

`P1`

## Why

Сейчас sprint close логика есть только как ручной endpoint/use case.

Для замены legacy поведения нужен backend job, который:
- регулярно проверяет группы;
- закрывает спринт автоматически;
- не дублирует закрытие;
- производит данные для дальнейших уведомлений.

## Goal

Перевести `sprint_results.py` из legacy в backend job infrastructure.

## Scope

- Добавить job module в backend.
- Добавить scheduler entrypoint.
- Реализовать периодическую проверку групп на окончание спринта.
- Вызывать существующий close use case через backend service.
- Зафиксировать политику timezone-aware выполнения.
- Логировать пропуски и повторные срабатывания.

## Acceptance Criteria

- backend может автоматически закрыть спринт без участия бота;
- повторный запуск job не приводит к двойному закрытию одного периода;
- job работает только через application services;
- есть integration-level tests на duplicate protection.

## Dependencies

- После Issue 02 и Issue 05.
- Перед Issue 07.

## Legacy References

- `UnitKeeperBot/sprint_results.py`

## Existing Backend References

- `backend/src/unitkeeper_backend/application/sprints/service.py`
- `backend/src/unitkeeper_backend/domain/services/sprint_math.py`
