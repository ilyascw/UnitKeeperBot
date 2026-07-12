# Issue Audit

Ревизия проведена 2026-07-12 по исходному коду, миграциям и доступным
локальным проверкам. Статус `partial` означает, что часть реализации есть,
но issue нельзя закрывать: не выполнен хотя бы один acceptance criterion.

## Summary

| Layer | Done | Partial | Not started |
| --- | --- | --- | --- |
| `common` | base schema, Issues 01-02 | Issue 03 | - |
| `backend` | archived Issues 01-05 | Issue 06 | Issues 07-09 |
| `miniapp` | archived Issues 01-03 | Issues 04-05 | - |
| `bot` | - | - | Issues 01-03 |

The ten completed issues are stored in `docs/archive` and explicitly marked
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
| 06: sprint close jobs and scheduler | partial | `SprintService.close_current_sprint` and a protected manual endpoint exist. There is no job module, scheduler entrypoint, due-group scan, scheduling policy, or duplicate-run integration test. |
| 07: notification outbox and deep links | not started | No persistent outbox, event producer, internal delivery endpoints, retry state machine, or deep-link contract exists. |
| 08: reminders, idempotency, observability and tests | not started | There are focused unit/API tests, but no reminder jobs, persistent idempotency, request/job correlation IDs, structured logging, DB integration tests, transfer tests, or notification tests. |
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
| 01: thin bot shell and backend transport | not started | `bot/` contains only `PLAN.md`; there is no package, configuration, Telegram application, backend client, handler, or test. |
| 02: approvals, notifications and deep links | not started | Depends on the missing backend outbox and thin bot shell. |
| 03: reports, reminders and fallback ops | not started | Depends on scheduler, outbox, reliability work, and the thin bot shell. |

## Verification Results

- `miniapp`: `npm run typecheck`, `npm run lint`, and `npm run build` pass.
- `backend`: Ruff passes and all 34 tests pass with the existing local import path setup. Backend-wide mypy and the default pytest invocation remain follow-up work.
- `common`: `make check` passes (Ruff, mypy, 4 tests) and `make test-migrations` passes against a disposable PostgreSQL database.

## Recommended Next Work

1. Complete `miniapp/Issue 04` with transfers and transfer history. The progress surface is already usable.
2. Implement `backend/Issues 06-08` in order: scheduler, persistent outbox/deep-link delivery contract, reminders/idempotency/observability.
3. Create the bot package and deliver `bot/Issues 01-03` only on those backend-owned contracts. Close with the coordinated `common/Issue 03` and `backend/Issue 09` cutover work.
4. Repair the backend quality gate: make the default test command and backend-wide mypy pass.
