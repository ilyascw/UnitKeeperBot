# Issue 03: Task Management Parity

**Status:** Closed and archived

## Priority

`P0`

## Why

Базовые task endpoints уже есть, но miniapp ещё не может закрыть task-management UX без доп. backend-функциональности.

Не хватает:
- bulk import;
- richer task detail contract;
- quick frequency adjustments;
- явного решения по admin-like `kill_tasks`.

## Goal

Закрыть backend parity по управлению задачами, чтобы miniapp не зависел от legacy bot handlers.

## Scope

- Довести task detail/read model до состояния, пригодного для экрана управления:
  - remaining executions in current sprint;
  - completed count;
  - deleted flag / deleted_at;
  - group ownership constraints.
- Добавить bulk import use case:
  - intake формата таблицы;
  - валидация колонок;
  - transactional import;
  - error report по строкам.
- Решить API для quick frequency adjustment:
  - либо отдельные actions;
  - либо через patch contract.
- Принять решение по `kill_tasks`:
  - либо backend admin endpoint;
  - либо явно оставить вне критического пути.

## Suggested API

- `POST /tasks/import`
- `GET /tasks/{task_id}`
- `PATCH /tasks/{task_id}`
- optionally `POST /tasks/{task_id}/increase-frequency`
- optionally `POST /tasks/{task_id}/decrease-frequency`

## Acceptance Criteria

- miniapp может создать, массово загрузить, просмотреть, изменить и soft-delete задачи;
- import не создаёт частично битые данные;
- task detail показывает оставшиеся выполнения в текущем спринте;
- решение по `kill_tasks` явно отражено в docs и plan;
- есть tests на import validation и task update semantics.

## Decision Log

- `kill_tasks` остаётся bot-only convenience. Backend не получает выделенного endpoint: массовое удаление выражается через повторный `DELETE /tasks/{task_id}` со стороны miniapp/bot. Аргумент — действие требует двухшагового подтверждения в UX и не относится к критическому пути API.
- `POST /tasks/import` принимает JSON-список (`items: [{title, frequency_per_sprint, unit_cost}]`); парсинг xlsx/csv остаётся на стороне клиента (miniapp/bot), backend получает только нормализованные строки. Импорт all-or-nothing: при наличии хотя бы одной невалидной строки возвращается `422` с `details.errors = [{index, field, message}, ...]` и ни одна задача не создаётся.
- Quick frequency adjustment реализован как явные actions `POST /tasks/{task_id}/increase-frequency` и `POST /tasks/{task_id}/decrease-frequency` с опциональным `{ "step": int > 0 }` (по умолчанию `1`). Soft-deleted задачи нельзя менять; уменьшение ниже `1` отклоняется `422`.

## Dependencies

- Может идти после Issue 02.

## Legacy References

- `UnitKeeperBot/handlers/add_task.py`
- `UnitKeeperBot/handlers/edit_task.py`
- `UnitKeeperBot/handlers/delete_task.py`
- `UnitKeeperBot/handlers/tasks.py`

## Existing Backend References

- `backend/src/unitkeeper_backend/application/tasks/service.py`
- `backend/src/unitkeeper_backend/api/routers/tasks.py`
