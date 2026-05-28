# Issue 03: Tasks And Approval Flows

## Priority

`P0`

## Why

Ежедневная ценность продукта живёт в task workflows, а они до сих пор сидят в legacy bot handlers.

Miniapp должен закрыть:
- task catalog;
- task management;
- mark done flow;
- pending approval surface.

## Goal

Перенести ежедневную task UX в miniapp без дублирования backend логики.

## Scope

- Task catalog и detail screen с remaining executions.
- Add/edit/soft-delete task flows.
- Quick frequency adjustment UX.
- Bulk import entrypoint и error presentation.
- Mark done UX с понятным pending/completed состоянием.
- Approval inbox/history screen как UI поверх backend `task_logs` read model.

## Acceptance Criteria

- пользователь управляет задачами без legacy `/add_task`, `/edit_task`, `/delete_task`, `/list_of_tasks`;
- miniapp показывает pending approvals и историю без прямого SQL или расчётов на клиенте;
- mark done / approve / reject используют только backend contracts;
- bulk import UX соответствует выбранному backend import contract.

## Dependencies

- После `docs/backend/issue-03-task-management-parity.md`.
- После `docs/backend/issue-04-task-approval-inbox-and-log-query-api.md`.

## Legacy References

- `UnitKeeperBot/handlers/add_task.py`
- `UnitKeeperBot/handlers/edit_task.py`
- `UnitKeeperBot/handlers/delete_task.py`
- `UnitKeeperBot/handlers/tasks.py`
