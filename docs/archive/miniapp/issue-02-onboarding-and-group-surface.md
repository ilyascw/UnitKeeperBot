# Issue 02: Onboarding And Group Surface

## Priority

`P0`

## Why

Legacy bot держит основной membership/group UX в командах `/start`, `/create_group`, `/join_group`, `/exit_group`, `/group_info`, `/group_settings`.

Это первый пользовательский срез, который miniapp должен забрать у legacy.

## Goal

Сделать miniapp основным интерфейсом для onboarding, membership и group management.

## Scope

- Экран без группы:
  - create group;
  - join group.
- Flows:
  - create group;
  - join group;
  - leave group.
- Group screen:
  - owner marker;
  - members;
  - weights;
  - sprint settings;
  - group balance.
- Owner-only settings UX.

## Acceptance Criteria

- пользователь без группы проходит onboarding без fallback на legacy handlers;
- current group screen покрывает `group_info` intent;
- owner может менять group settings через miniapp;
- leave group flow явно обрабатывает owner handover сценарий.

## Dependencies

- После `docs/archive/backend/issue-02-group-read-and-settings-api.md`.

## Legacy References

- `UnitKeeperBot/handlers/start.py`
- `UnitKeeperBot/handlers/group.py`
- `UnitKeeperBot/handlers/join_group.py`
- `UnitKeeperBot/handlers/exit_group.py`
- `UnitKeeperBot/handlers/group_info.py`
- `UnitKeeperBot/handlers/group_settings.py`
