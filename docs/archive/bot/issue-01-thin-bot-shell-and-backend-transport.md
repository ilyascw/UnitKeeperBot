# Issue 01: Thin Bot Shell And Backend Transport

**Status:** Closed and archived

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

- [x] Bootstrap bot app structure и config.
- [x] Подключить backend internal transport/auth.
- [x] Реализовать:
  - `/start`;
  - `/help`;
  - `/about`;
  - fallback для команд, переехавших в miniapp.
- [x] Добавить ensure-user/current-context path через backend, а не прямую БД.

## Acceptance Criteria

- [x] bot не содержит прямых бизнес-решений для group/task/balance flows;
- [x] `/start` открывает miniapp и умеет инициализировать пользователя через backend;
- [x] unsupported legacy commands получают понятный redirect в miniapp;
- [x] transport/auth bot -> backend задокументирован и покрыт минимальными тестами.

## Dependencies

- После `docs/archive/backend/issue-01-bot-auth-and-backend-transport.md`.

## Legacy References

- `UnitKeeperBot/handlers/start.py`
- `UnitKeeperBot/handlers/help.py`
- `UnitKeeperBot/handlers/about.py`
