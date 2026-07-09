# Backend Delivery Backlog

## Purpose

Этот backlog фиксирует, что ещё нужно реализовать на backend, чтобы:

1. miniapp мог опираться на полноценный API без бизнес-логики на клиенте;
2. bot стал тонким слоем уведомлений и fallback-команд, а не местом, где живут правила продукта;
3. миграция с legacy-бота шла задачами, которые можно брать в работу независимо.

Источники:
- `docs/legacy-functionality.md`
- `backend/PLAN.md`
- текущий код в `backend/src/unitkeeper_backend`

## Что уже есть в backend

В коде уже заложен первый рабочий срез:
- FastAPI app, роутер и централизованное domain error mapping;
- DI через Dishka для config, clock, session, UoW и сервисов;
- auth через Telegram Mini App init data;
- internal bot transport через service secret;
- current user / current group context;
- create / join / leave group;
- детальный group read/settings API;
- tasks CRUD, bulk import и quick frequency adjustments;
- mark done / approve / reject;
- temp results;
- manual current sprint close с защитой от повторного закрытия периода.

## Что ещё мешает писать miniapp и thin bot

Критические пробелы:
- нет approval inbox / query API для task logs;
- нет balances / transfers;
- нет scheduler jobs и notification outbox;
- нет deep link и delivery-контрактов для бота;
- нет reminder jobs;
- нет полного покрытия тестами, idempotency и observability.

## Очередь задач

`P0`
- [Issue 04](./issue-04-task-approval-inbox-and-log-query-api.md) Approval inbox и task log query API
- [Issue 05](./issue-05-balances-and-unit-transfers.md) Balances и unit transfers

`P1`
- [Issue 06](./issue-06-sprint-close-jobs-and-scheduler.md) Sprint close jobs и scheduler
- [Issue 07](./issue-07-notification-outbox-and-deep-links.md) Notification outbox и deep links
- [Issue 08](./issue-08-reminders-idempotency-observability-and-tests.md) Reminders, idempotency, observability, tests

`P2`
- [Issue 09](./issue-09-admin-ops-and-legacy-cutover.md) Admin/ops parity и финальный cutover legacy bot

## Suggested execution order

1. Issue 04
2. Issue 05
3. Issue 06
4. Issue 07
5. Issue 08
6. Issue 09

## Archived

- [Issue 01](../archive/backend/issue-01-bot-auth-and-backend-transport.md) Bot auth и internal transport
- [Issue 02](../archive/backend/issue-02-group-read-and-settings-api.md) Group read/settings API
- [Issue 03](../archive/backend/issue-03-task-management-parity.md) Task management parity

## Notes

- Если задача меняет поведение относительно legacy, это должно быть явно зафиксировано в issue и в PR.
- Всё новое продуктовое поведение должно жить в backend application services, а не в bot handlers или miniapp UI.
- Если задача зависит от новых DB сущностей или миграций, они должны идти через `common`.
