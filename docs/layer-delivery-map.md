# Layer Delivery Map

## Purpose

Этот документ фиксирует согласованную очередь работ между слоями `common`, `backend`, `miniapp` и `bot`, чтобы:

1. не брать UI-задачи раньше готовых backend-контрактов;
2. не пропустить нужные schema changes в `common`;
3. держать bot тонким, а miniapp главным интерфейсом.

## Recommended Execution Order

1. `common/Issue 01` -> добить качество shared DB слоя и миграционный smoke path.
2. `backend/Issue 01` -> зафиксировать transport и auth для thin bot.
3. `backend/Issue 02` -> закрыть group read/settings API.
4. `miniapp/Issue 01` -> поднять shell на `Vite + React + TypeScript + Telegram UI Kit`.
5. `backend/Issue 03` -> довести task management parity.
6. `backend/Issue 04` -> добавить approval inbox и task log query API.
7. `backend/Issue 05` -> реализовать balances и unit transfers.
8. `miniapp/Issue 02`, `miniapp/Issue 03`, `miniapp/Issue 04` -> строить основные пользовательские экраны поверх готового API.
9. `common/Issue 02` -> добавить schema support для outbox/idempotency delivery.
10. `backend/Issue 06`, `backend/Issue 07`, `backend/Issue 08` -> jobs, outbox, reminders, reliability.
11. `bot/Issue 01`, `bot/Issue 02`, `bot/Issue 03` -> подключать thin bot к backend-owned contracts.
12. `miniapp/Issue 05`, `common/Issue 03`, `backend/Issue 09` -> hardening, cutover и финальная миграция.

## Coordination Rules

- `common` идёт первым, когда задача требует новой таблицы, индекса, enum или миграции.
- `backend` открывает контракты для `miniapp` и `bot`; клиентские слои не должны изобретать данные или правила локально.
- `miniapp` не берёт экран в активную разработку, пока не зафиксирован backend response shape для него.
- `bot` не читает и не пишет бизнес-данные напрямую; только через backend internal transport и backend-owned events.
- Если issue меняет product behavior относительно `docs/legacy-functionality.md`, это должно быть явно помечено в соответствующем issue.

## Current Reality Check

- `common` уже закрывает базовый schema slice: users, groups, memberships, weights, tasks, task logs, balances, ledger, sprint runs.
- `backend` уже закрывает auth для miniapp, current context, group create/join/leave, tasks CRUD, done/approve/reject, temp results и manual sprint close.
- Основные незакрытые зависимости сейчас лежат в group settings, task import/history, balances, scheduler/outbox и thin-bot transport.
