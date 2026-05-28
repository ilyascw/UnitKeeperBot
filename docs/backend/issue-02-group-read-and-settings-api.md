# Issue 02: Group Read And Settings API

## Priority

`P0`

## Why

Для miniapp недостаточно только `GET /groups/current`.

Нужны:
- детальная group card;
- member list с балансами и весами;
- derived sprint info;
- owner-only settings update API.

Сейчас это ещё живёт в legacy `group_info` и `group_settings`.

## Goal

Перенести в backend весь group read/write слой, который нужен miniapp и bot fallback.

## Scope

- Добавить расширенное чтение текущей группы:
  - owner;
  - members;
  - active weights;
  - member balances;
  - current sprint window;
  - current sprint end date;
  - group balance.
- Добавить owner-only update endpoints:
  - change join secret;
  - change sprint start weekday;
  - change sprint duration;
  - change member weights.
- Вынести в backend валидацию веса:
  - только активные участники;
  - сумма = 100;
  - отрицательные веса запрещены.
- Зафиксировать политику при изменении состава участников после ручной настройки веса.

## Suggested API

- `GET /groups/current`
- `GET /groups/current/members`
- `PATCH /groups/current/settings`
- `PUT /groups/current/weights`

## Acceptance Criteria

- miniapp может показать полную карточку группы без обращений к legacy логике;
- только owner может менять group settings;
- backend валидирует сумму весов и состав участников;
- API возвращает достаточно данных для screen group info/settings;
- есть unit и API tests на owner / non-owner сценарии.

## Dependencies

- Желательно после Issue 01, но можно вести параллельно.

## Legacy References

- `UnitKeeperBot/handlers/group_info.py`
- `UnitKeeperBot/handlers/group_settings.py`

## Existing Backend References

- `backend/src/unitkeeper_backend/application/groups/service.py`
- `backend/src/unitkeeper_backend/api/routers/groups.py`
- `backend/src/unitkeeper_backend/domain/services/sprint_math.py`
