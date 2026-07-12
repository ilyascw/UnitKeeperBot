# Issue 01: Bot Auth And Backend Transport

**Status:** Closed and archived

## Priority

`P0`

## Why

Сейчас backend умеет аутентифицировать miniapp через Telegram init data, но план всё ещё не закрывает вопрос, как thin bot будет безопасно ходить в backend.

Без этого:
- bot продолжит тянуть бизнес-логику к себе;
- нельзя чисто реализовать `/start`, approval notifications и reminder flows;
- miniapp и bot не смогут опираться на одну backend-модель действий.

## Goal

Согласовать и реализовать transport между bot и backend, при котором:
- bot использует service-level auth, а не пользовательский miniapp token;
- backend остаётся единственным владельцем бизнес-правил;
- bot может выполнять только разрешённые internal операции;
- пользовательские действия по кнопкам и deep links валидируются backend.

## Scope

- Выбрать и задокументировать способ bot -> backend auth.
- Добавить internal API surface для бота.
- Добавить backend use case для bootstrap/ensure user из Telegram profile без miniapp init data.
- Определить, как bot выполняет user-scoped actions:
  - либо через signed action tokens;
  - либо через internal endpoint с явной передачей `actor_user_id` и backend-проверкой.
- Добавить минимальный audit trail для internal bot requests.

## Suggested API / design

- `POST /internal/bot/users/ensure`
- `GET /internal/bot/users/{telegram_user_id}/context`
- `POST /internal/bot/task-logs/{task_log_id}/approve`
- `POST /internal/bot/task-logs/{task_log_id}/reject`
- internal auth header по service secret или signed machine token

## Acceptance Criteria

- bot может зарегистрировать или обновить пользователя без прямого доступа к БД;
- bot может получить current context пользователя через backend;
- backend различает miniapp user auth и bot service auth;
- user-scoped actions через bot проходят через backend authorization rules;
- internal endpoints не доступны обычным клиентским токенам;
- есть тесты на happy path и forbidden path.

## Dependencies

- Может идти первой.

## Legacy References

- `UnitKeeperBot/handlers/start.py`
- `UnitKeeperBot/handlers/tasks.py`

## Existing Backend References

- `backend/src/unitkeeper_backend/application/auth/service.py`
- `backend/src/unitkeeper_backend/api/routers/auth.py`
- `backend/src/unitkeeper_backend/di.py`
