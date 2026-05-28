# Issue 01: Thin Bot Shell And Backend Transport

## Priority

`P0`

## Why

Пока bot не умеет безопасно работать через backend, любой следующий bot flow будет тянуть бизнес-логику обратно в handlers.

## Goal

Поднять минимальный bot shell, который:
- умеет делать `/start`, `/help`, `/about` и fallback replies;
- ходит только в backend contracts;
- открывает miniapp как основной пользовательский surface.

## Scope

- Bootstrap bot app structure и config.
- Подключить backend internal transport/auth.
- Реализовать:
  - `/start`;
  - `/help`;
  - `/about`;
  - fallback для команд, переехавших в miniapp.
- Добавить ensure-user/current-context path через backend, а не прямую БД.

## Acceptance Criteria

- bot не содержит прямых бизнес-решений для group/task/balance flows;
- `/start` открывает miniapp и умеет инициализировать пользователя через backend;
- unsupported legacy commands получают понятный redirect в miniapp;
- transport/auth bot -> backend задокументирован и покрыт минимальными тестами.

## Dependencies

- После `docs/backend/issue-01-bot-auth-and-backend-transport.md`.

## Legacy References

- `UnitKeeperBot/handlers/start.py`
- `UnitKeeperBot/handlers/help.py`
- `UnitKeeperBot/handlers/about.py`
