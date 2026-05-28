# Issue 07: Notification Outbox And Deep Links

## Priority

`P1`

## Why

Thin bot с уведомлениями невозможен без backend-owned notification contract.

Нужны:
- событие о pending approval;
- событие о rejection/approval;
- событие о sprint close;
- deep link payload, по которому bot отправляет пользователя в miniapp.

## Goal

Сделать outbox/event слой, который отделяет backend business events от bot delivery.

## Scope

- Определить persistent outbox модель в `common` или backend-owned store.
- Генерировать события при:
  - mark done -> pending approval;
  - approve;
  - reject;
  - sprint close;
  - reminder conditions.
- Определить delivery contract для bot worker:
  - fetch unsent events;
  - mark delivered / failed;
  - retry semantics.
- Определить deep link format для miniapp navigation.

## Suggested API / transport

- `GET /internal/bot/notifications/outbox`
- `POST /internal/bot/notifications/{event_id}/ack`
- `POST /internal/bot/notifications/{event_id}/fail`

## Acceptance Criteria

- bot получает все пользовательские уведомления из backend, а не вычисляет их сам;
- события не теряются и не дублируются бесконтрольно;
- каждое событие содержит достаточно данных для текста уведомления и deep link;
- есть documented event types и delivery states.

## Dependencies

- После Issue 01, Issue 04 и Issue 06.

## Legacy References

- `UnitKeeperBot/handlers/tasks.py`
- `UnitKeeperBot/sprint_results.py`

## Existing Backend References

- `backend/src/unitkeeper_backend/application/tasks/service.py`
- `backend/src/unitkeeper_backend/application/sprints/service.py`
