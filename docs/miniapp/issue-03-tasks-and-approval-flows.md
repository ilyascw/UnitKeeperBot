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

- [x] Task catalog с remaining executions.
- [x] Task detail surface с completed / pending / available counts.
- [x] Add task flow.
- [x] Edit task flow.
- [x] Soft-delete task flow с явным подтверждением.
- [x] Quick frequency adjustment UX (`+1` / `-1`) для владельца.
- [x] Mark done UX с pending/completed/limit состояниями.
- [ ] Bulk import entrypoint и error presentation.
- [ ] Approval inbox/history screen как UI поверх backend `task_logs` read model.

## Current Done Slice

Закрытая часть реализована в miniapp поверх уже существующих backend contracts:

- `GET /tasks`;
- `POST /tasks`;
- `PATCH /tasks/{task_id}`;
- `DELETE /tasks/{task_id}`;
- `POST /tasks/{task_id}/increase-frequency`;
- `POST /tasks/{task_id}/decrease-frequency`;
- `POST /tasks/{task_id}/done`.

Файлы:

- `miniapp/src/api/endpoints.ts`
- `miniapp/src/api/mutations.ts`
- `miniapp/src/api/types.ts`
- `miniapp/src/screens/TasksScreen.tsx`
- `miniapp/src/ui/icons.tsx`

Проверки:

- `npm run typecheck`
- `npm run lint`
- `npm run build`

## Remaining Work

- Bulk import UI:
  - выбрать формат miniapp entrypoint для spreadsheet/manual paste;
  - отправлять данные в `POST /tasks/import`;
  - показать row-level validation errors из backend.
- Approval inbox/history:
  - зависит от `docs/backend/issue-04-task-approval-inbox-and-log-query-api.md`;
  - нужен список pending approvals;
  - нужны approve/reject actions с reject reason;
  - нужна history surface для completed/rejected logs.

## Acceptance Criteria

- [x] Пользователь видит task catalog без legacy `/list_of_tasks`.
- [x] Владелец добавляет, редактирует, удаляет задачи и меняет частоту без legacy `/add_task`, `/edit_task`, `/delete_task`.
- [x] Mark done использует только backend contract.
- [ ] Miniapp показывает pending approvals и историю без прямого SQL или расчётов на клиенте.
- [ ] Approve / reject используют только backend contracts.
- [ ] Bulk import UX соответствует выбранному backend import contract.

## Dependencies

- После `docs/archive/backend/issue-03-task-management-parity.md`.
- После `docs/backend/issue-04-task-approval-inbox-and-log-query-api.md`.

## Legacy References

- `UnitKeeperBot/handlers/add_task.py`
- `UnitKeeperBot/handlers/edit_task.py`
- `UnitKeeperBot/handlers/delete_task.py`
- `UnitKeeperBot/handlers/tasks.py`
