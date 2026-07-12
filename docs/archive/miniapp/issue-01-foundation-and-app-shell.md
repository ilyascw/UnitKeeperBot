# Issue 01: Foundation And App Shell

**Status:** Closed and archived

## Priority

`P0`

## Why

Без единого frontend foundation дальше нельзя собирать экраны последовательно и без хаоса.

Платформенное решение для miniapp нужно зафиксировать сейчас, чтобы не прыгать между стеками.

## Goal

Поднять miniapp shell на согласованном стеке:
- `Vite`
- `React`
- `TypeScript`
- `Telegram UI Kit`

## Scope

- Bootstrap project structure под Telegram Mini App runtime.
- Настроить routing, screen layout и shared app shell.
- Интегрировать Telegram UI Kit и базовые design tokens.
- Добавить API client, auth bootstrap от Telegram init data и session restore.
- Подготовить error boundary, loading states и env/config surface.

## Acceptance Criteria

- miniapp стартует как Telegram Mini App на выбранном стеке;
- есть базовый routing shell и layout container для экранов;
- auth bootstrap не требует ручной передачи user id в API;
- Telegram UI Kit используется как основа интерфейса, а не как случайная точечная зависимость;
- developer setup задокументирован.

## Dependencies

- Может идти параллельно с `docs/archive/backend/issue-02-group-read-and-settings-api.md`, но без привязки к неготовым screen contracts.

## References

- `miniapp/PLAN.md`
- `docs/legacy-functionality.md`
