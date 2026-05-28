# Common Delivery Backlog

## Purpose

Этот backlog описывает, что ещё нужно в `common`, поверх уже готового базового shared DB слоя.

Источники:
- `common/PLAN.md`
- `common/README.md`
- `common/ARCHITECTURE.md`
- `docs/legacy-functionality.md`
- `docs/layer-delivery-map.md`

## What Is Already Done

В `common` уже есть рабочий первый срез:
- SQLAlchemy 2 models для users, groups, memberships, weights, tasks, task logs, balances, ledger и sprint runs;
- Alembic baseline migration;
- async engine, sessionmaker и transaction helpers;
- нормализация legacy `weights` JSON, `group_balance` inconsistency и sprint bookkeeping;
- package surface, который уже использует backend.

## What Is Still Missing

Критические пробелы:
- нет schema/test hardening вокруг миграций и package contract;
- нет outbox/idempotency storage для bot delivery и repeated callbacks;
- нет продуманной legacy bootstrap/cutover стратегии.

## Queue

`P0`
- [Issue 01](./issue-01-package-hardening-and-migration-smoke.md) Package hardening и migration smoke

`P1`
- [Issue 02](./issue-02-outbox-and-idempotency-schema.md) Outbox, delivery state и idempotency schema

`P2`
- [Issue 03](./issue-03-legacy-bootstrap-and-cutover-support.md) Legacy bootstrap, migration policy и cutover support

## Notes

- `common` не должен забирать бизнес-логику у backend.
- Новые schema additions должны сначала подтверждаться задачами в `backend`, `bot` или `miniapp`, а не появляться спекулятивно.
