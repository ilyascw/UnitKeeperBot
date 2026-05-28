# Issue 03: Legacy Bootstrap And Cutover Support

## Priority

`P2`

## Why

Даже после готовых schema и API останется вопрос, как безопасно перейти с legacy bot data/processes на новый стек.

Сейчас в `common` не хватает:
- стратегии initial import или bootstrap;
- зафиксированной migration policy для следующих schema changes;
- cutover support для финального выключения старой ORM-логики.

## Goal

Подготовить `common` к управляемому cutover, а не только к greenfield development.

## Scope

- Описать стратегию работы с существующими legacy данными.
- Решить, нужны ли bootstrap scripts или explicit import contracts.
- Зафиксировать правила для следующих Alembic revisions и backwards-compatible rollouts.
- Подготовить schema-side checklist для `backend/Issue 09`.

## Acceptance Criteria

- есть понятная стратегия initial data/bootstrap;
- future migrations имеют documented policy;
- финальный cutover не требует ручного угадывания состояния БД;
- документация ссылается на реальные backend/bot cutover tasks.

## Dependencies

- После `common/Issue 01`.
- Лучше синхронизировать с `backend/Issue 09`.

## References

- `docs/backend/issue-09-admin-ops-and-legacy-cutover.md`
- `docs/legacy-functionality.md`
