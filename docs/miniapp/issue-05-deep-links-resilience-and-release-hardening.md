# Issue 05: Deep Links, Resilience, And Release Hardening

## Priority

`P1`

## Why

После появления основных экранов miniapp ещё нужно довести до production-like поведения внутри Telegram:
- deep links из bot notifications;
- graceful handling auth expiry и reconnect;
- проверка поведения в in-app browser.

## Goal

Сделать miniapp устойчивым как основной продуктовый surface, а не только набором экранов.

## Scope

- Deep-link routing из bot notification payloads.
- Обработка expired session и re-auth.
- Empty/error/offline states для частичных API failures.
- QA на мобильном layout и Telegram in-app browser behavior.
- Release checklist для первого usable launch.

## Acceptance Criteria

- bot может открыть пользователя в точный экран miniapp;
- повторный вход и ошибки API не ломают навигацию;
- UI проверен под мобильный Telegram сценарий как базовый.

## Dependencies

- После `docs/backend/issue-07-notification-outbox-and-deep-links.md`.
- После `docs/backend/issue-08-reminders-idempotency-observability-and-tests.md`.
- Сильно связана с `docs/archive/bot/issue-02-approvals-notifications-and-deep-links.md`.

## References

- `miniapp/PLAN.md`
- `docs/layer-delivery-map.md`
