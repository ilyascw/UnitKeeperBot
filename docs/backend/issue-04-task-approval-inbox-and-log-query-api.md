# Issue 04: Task Approval Inbox And Log Query API

## Priority

`P0`

## Why

Approve/reject endpoints сами по себе недостаточны.

Для miniapp inbox и thin bot notifications нужны query endpoints:
- список pending approvals для пользователя;
- детали pending/completed/rejected log;
- история task logs по группе и пользователю;
- payload для уведомлений и deep links.

## Goal

Сделать `task_logs` first-class read model в backend.

## Scope

- Добавить read API для task logs:
  - pending approvals for current user;
  - own recent executions;
  - group-level task log history;
  - detail by id.
- Обогатить task log response:
  - performer summary;
  - task summary;
  - created/decided timestamps;
  - status;
  - rejection reason.
- Определить фильтры и pagination.
- Подготовить response shape, пригодный и для miniapp, и для bot notification worker.

## Suggested API

- `GET /task-logs/pending-approval`
- `GET /task-logs/mine`
- `GET /task-logs/{task_log_id}`
- `GET /groups/current/task-logs`

## Acceptance Criteria

- bot может получить список задач, которые надо показать на подтверждение;
- miniapp может построить inbox и history screens без повторения бизнес-логики;
- approve/reject workflow не требует прямого SQL в bot;
- rejected logs сохраняют reason и доступны в history;
- есть tests на visibility rules и filters.

## Dependencies

- После Issue 01.
- Сильно связана с Issue 07.

## Legacy References

- `UnitKeeperBot/handlers/tasks.py`

## Existing Backend References

- `backend/src/unitkeeper_backend/application/tasks/service.py`
- `backend/src/unitkeeper_backend/infrastructure/repositories/tasks.py`
