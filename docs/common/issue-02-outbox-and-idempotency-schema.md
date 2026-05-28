# Issue 02: Outbox And Idempotency Schema

## Priority

`P1`

## Why

Следующие backend/bot задачи требуют persistence support, которого в `common` пока нет:
- notification outbox;
- delivery state для bot worker;
- idempotency keys для repeated callbacks и retries;
- job bookkeeping beyond current sprint-run uniqueness.

Без этого `backend/Issue 07` и `backend/Issue 08` останутся либо in-memory, либо размажут storage решения по другим слоям.

## Goal

Добавить в `common` schema primitives для backend-owned events, delivery attempts и idempotent write flows.

## Scope

- Спроектировать и добавить таблицы для:
  - notification outbox;
  - delivery attempts / ack / fail state;
  - idempotency keys и request fingerprints, если выбран persistent подход.
- Зафиксировать enums/statuses для delivery lifecycle.
- Добавить Alembic migration и обновить schema docs.
- Не переносить в `common` сам delivery worker и не писать здесь бизнес-оркестрацию.

## Acceptance Criteria

- backend может хранить pending notification events без bot-side SQL;
- bot worker может ack/fail delivery через backend поверх понятной persistent модели;
- repeated external actions можно дедуплицировать на storage уровне;
- новые сущности документированы и не конфликтуют с текущим schema slice.

## Dependencies

- Лучше после `common/Issue 01`.
- Нужна до `backend/Issue 07` и `backend/Issue 08`.

## References

- `docs/backend/issue-07-notification-outbox-and-deep-links.md`
- `docs/backend/issue-08-reminders-idempotency-observability-and-tests.md`
- `docs/bot/issue-02-approvals-notifications-and-deep-links.md`
