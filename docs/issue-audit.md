# Issue Audit

Ревизия проведена 2026-07-12 по исходному коду, миграциям и доступным
локальным проверкам. Статус `partial` означает, что часть реализации есть,
но issue нельзя закрывать: не выполнен хотя бы один acceptance criterion.

## Summary

| Layer | Done | Partial | Not started |
| --- | --- | --- | --- |
| `common` | base schema, Issues 01-02 | Issue 03 | - |
| `backend` | archived Issues 01-05 | Issues 06-08 | Issue 09 |
| `miniapp` | archived Issues 01-03 | Issues 04-05 | - |
| `bot` | Issues 01-03 | - | - |

The thirteen completed issues are stored in `docs/archive` and explicitly marked
`Closed and archived`. Common Issue 02, Backend Issue 05 and Miniapp Issue 03
were implemented, verified and moved after the second delivery pass.

## Evidence By Issue

### Common

| Issue | Status | Evidence and remaining work |
| --- | --- | --- |
| 01: package hardening and migration smoke | done | Archived after adding uv dev tooling, documented Make targets, package-surface tests and a fresh PostgreSQL migration smoke test. Ruff, mypy and all tests pass. |
| 02: outbox and idempotency schema | done | Archived after adding persistent outbox events, delivery attempts, idempotency keys, enums, schema documentation and Alembic migration `20260712_0002`. |
| 03: legacy bootstrap and cutover support | partial | Revisions `20260315_0000` and `20260315_0001` transform legacy data; `docs/common/legacy-data-bootstrap.md` documents data-only and full-schema dumps. A forward migration policy, validated bootstrap run, and cross-layer cutover checklist are still absent. |

### Backend

| Issue | Status | Evidence and remaining work |
| --- | --- | --- |
| 01-03: archived baseline | done | Auth, internal bot transport, group APIs, task CRUD/import, task completion/approval/rejection, temp results and manual sprint close are present. |
| 04: task approval inbox and log query API | done | Archived after adding pending-approval, personal history, group history and detail read endpoints with enriched paginated responses, visibility rules and filter coverage. |
| 05: balances and unit transfers | done | Archived after adding balance, transfer-candidate, transfer and transaction-history APIs; transfers lock balances, prevent invalid operations and write paired ledger rows. |
| 06: sprint close jobs and scheduler | partial | Application job orchestration and duplicate-close tests now exist, but runtime scheduler startup, due-group scanning and scheduling policy are still absent. |
| 07: notification outbox and deep links | partial | Persistent outbox, task event producers, internal fetch/ack/fail endpoints, retries, dedupe/correlation and deep links are implemented. Sprint-close publication still needs runtime scheduler wiring. |
| 08: reminders, idempotency, observability and tests | partial | Backend reminder publishers use deterministic dedupe keys and correlation IDs, with notification tests. Request tracing, generalized write idempotency, DB integration coverage and production job lifecycle remain open. |
| 09: admin ops and legacy cutover | not started | No admin/fallback decision for `kill_tasks`, no cutover checklist, and the replacement thin bot does not yet exist. |

### Miniapp

| Issue | Status | Evidence and remaining work |
| --- | --- | --- |
| 01-02: archived baseline | done | React/Vite Telegram app shell plus onboarding, create/join/leave group, group information, settings and weights are implemented. |
| 03: tasks and approval flows | done | Archived after adding bulk import, approval inbox/history and approve/reject UI over backend contracts. |
| 04: balances, progress and content | partial | `/progress` uses sprint results and renders a completed-task breakdown. `/balance` displays balances from the current group read model. Transfers, transaction history, and help/about content are absent; the current balance view is not the transfer flow required by the issue. |
| 05: deep links, resilience and release hardening | partial | Shared error states, retry actions, an error boundary, and session bootstrap exist. There is no notification deep-link parser/router, no explicit expired-session recovery, no Telegram mobile QA record, and no release checklist. |

### Bot

| Issue | Status | Evidence and remaining work |
| --- | --- | --- |
| 01: thin bot shell and backend transport | done | Archived after adding the aiogram service shell, backend-only transport, `/start`, `/help`, `/about`, fallback redirects, configuration and tests. |
| 02: approvals, notifications and deep links | done | Archived after adding backend-owned approval events, outbox polling, inline approve/reject actions, exact Mini App links and ack/fail delivery handling. |
| 03: reports, reminders and fallback ops | done | Archived after adding sprint/reminder/group-event rendering, backend job publishers, durable dedupe/correlation, owner-handover notifications and a recovery runbook. |

## Verification Results

- `miniapp`: `npm run typecheck`, `npm run lint`, and `npm run build` pass.
- `backend`: Ruff passes and all 37 tests pass with the existing local import path setup. Backend-wide mypy and the default pytest invocation remain follow-up work.
- `bot`: Ruff, mypy and all 9 tests pass from the service-local virtual environment.
- `common`: Ruff, mypy and 4 non-integration tests pass; migrations through `20260712_0003` pass against disposable PostgreSQL.

## Recommended Next Work

1. Complete `miniapp/Issue 04` with transfers and transfer history. The progress surface is already usable.
2. Finish runtime scheduler wiring in `backend/Issue 06`, then close the remaining reliability gaps in Issues 07-08.
3. Close the coordinated `common/Issue 03` and `backend/Issue 09` legacy cutover work.
4. Repair the backend quality gate: make the default test command and backend-wide mypy pass.
