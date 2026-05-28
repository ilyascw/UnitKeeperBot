# Issue 01: Package Hardening And Migration Smoke

## Priority

`P0`

## Why

Базовый schema slice уже реализован, но слой ещё не доведён до надёжного shared foundation.

Сейчас не хватает:
- миграционного smoke path;
- минимального test harness вокруг схемы;
- зафиксированного developer workflow для `ruff`, `mypy`, `uv`, migrations.

## Goal

Сделать `common` устойчивым базовым пакетом, на который можно спокойно опираться из backend и будущего thin bot.

## Scope

- Проверить и зафиксировать `uv`-based workflow внутри `common/.venv`.
- Добавить smoke checks на:
  - import package surface;
  - create metadata / run migrations;
  - upgrade fresh database.
- Подготовить минимальный test setup для schema-level assertions.
- Зафиксировать developer commands в docs и Make targets, если сейчас чего-то не хватает.

## Acceptance Criteria

- `common` поднимается и мигрируется предсказуемо по документации;
- есть автоматическая проверка, что baseline migration применима на чистую БД;
- package surface не ломается незаметно при следующих изменениях;
- developer workflow для `uv`, `ruff`, `mypy`, tests описан без двусмысленностей.

## Dependencies

- Может идти первой.

## References

- `common/PLAN.md`
- `common/README.md`
- `common/alembic/versions/20260315_0001_initial_unitkeeper_schema.py`
