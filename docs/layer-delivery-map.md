# Layer Delivery Map

## Purpose

Этот документ фиксирует согласованную очередь работ между слоями `common`, `backend`, `miniapp` и `bot`, чтобы:

1. не брать UI-задачи раньше готовых backend-контрактов;
2. не пропустить нужные schema changes в `common`;
3. держать bot тонким, а miniapp главным интерфейсом.

## Recommended Execution Order

1. `miniapp/Issue 04` -> завершить transfers/history UI поверх готового balances API.
2. `backend/Issue 06`, `backend/Issue 07`, `backend/Issue 08` -> jobs, outbox, reminders, reliability.
3. `bot/Issue 01`, `bot/Issue 02`, `bot/Issue 03` -> подключать thin bot к backend-owned contracts.
4. `miniapp/Issue 05`, `common/Issue 03`, `backend/Issue 09` -> hardening, cutover и финальная миграция.

## Archived As Done

- `backend/Issue 01` -> bot auth и internal backend transport.
- `backend/Issue 02` -> group read/settings API.
- `backend/Issue 03` -> task management parity.
- `backend/Issue 04` -> task approval inbox и task-log query API.
- `backend/Issue 05` -> balances и unit transfers.
- `common/Issue 01` -> package hardening и migration smoke path.
- `common/Issue 02` -> outbox и idempotency schema.
- `miniapp/Issue 01` -> `Vite + React + TypeScript + Telegram UI Kit` shell.
- `miniapp/Issue 02` -> onboarding и group surface.
- `miniapp/Issue 03` -> tasks, execution и approval flows.

## Coordination Rules

- `common` идёт первым, когда задача требует новой таблицы, индекса, enum или миграции.
- `backend` открывает контракты для `miniapp` и `bot`; клиентские слои не должны изобретать данные или правила локально.
- `miniapp` не берёт экран в активную разработку, пока не зафиксирован backend response shape для него.
- `bot` не читает и не пишет бизнес-данные напрямую; только через backend internal transport и backend-owned events.
- Если issue меняет product behavior относительно `docs/legacy-functionality.md`, это должно быть явно помечено в соответствующем issue.

## Current Reality Check

- `common` уже закрывает базовый schema slice, migration smoke, persistent outbox и idempotency primitives.
- `backend` уже закрывает auth для miniapp, internal bot auth/transport, current context, group create/join/leave/settings, tasks CRUD/import, done/approve/reject, task-log inbox/history/detail, balances/transfers, temp results и manual sprint close.
- `miniapp` уже закрывает app shell, onboarding, create/join/leave group, group info, settings, weights и task approval flows.
- Основные незакрытые зависимости сейчас лежат в transfer/history UI, scheduler/outbox delivery, reminder jobs и реализации thin bot.
