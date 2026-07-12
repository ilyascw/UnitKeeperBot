# Backend Plan

## Goal
- Move all business rules into a FastAPI service.
- Backend becomes the only place that knows product logic.

## Scope
- FastAPI app, Dishka DI, business services, auth, scheduler orchestration, and integrations.

## Phase 1: Service Foundation
- [x] Bootstrap FastAPI application structure.
- [x] Wire Dishka containers for config, DB sessions, repositories, and core services.
- [ ] Add background-job providers and worker startup lifecycle.
- [x] Add health endpoint and local developer run path.
- [x] Define public API shape before implementing screens.

## Phase 2: Auth And Session Context
- [x] Verify Telegram Mini App init data on the backend.
- [x] Resolve or create local user records from Telegram identity.
- [x] Provide current-user and current-group context dependencies.
- [x] Decide whether the bot also authenticates through service credentials or internal transport. *(Issue 01: service-secret via `X-Internal-Auth` header on `/api/v1/internal/bot/*`)*

## Phase 3: Core Use Cases
- [x] Create, join, and leave group with owner handover rules.
- [x] Read current user/current group context and base group summary.
- [x] Update group settings. *(Issue 02: `GET /groups/current` card, `GET /groups/current/members`, `PATCH /groups/current/settings`, `PUT /groups/current/weights`; manual weights reset on join/leave via equal redistribution.)*
- [x] Create, read, update, soft-delete, and list tasks.
- [x] Add bulk import and richer task-management contracts. *(Issue 03: `POST /tasks/import` with per-row validation report, `POST /tasks/{id}/increase-frequency`, `POST /tasks/{id}/decrease-frequency`; legacy `kill_tasks` intentionally left as a bot-only convenience and excluded from backend critical path.)*
- [x] Compute remaining task executions within the current sprint.
- [x] Mark task completion.
- [x] Approve or reject task completion.
- [x] Read sprint progress and current results.
- [x] Read balance, transfer units, and expose transfer history. *(Issue 05: `/balances/me`, `/balances/transfer-candidates`, `/balances/transfers`, `/balances/transactions`.)*

## Phase 4: Scheduling And Notifications
- [x] Expose manual current-sprint close use case with duplicate protection.
- [ ] Rebuild sprint closing logic as backend jobs.
- [x] Store scheduler-safe bookkeeping to avoid duplicate sprint closure.
- [x] Produce notification events for the bot.
- [x] Produce deep links for miniapp navigation from notifications.
- [x] Add reminder jobs for pending confirmations and sprint deadlines.

## Phase 5: Reliability
- [x] Add validation and business error taxonomy.
- [x] Add initial unit tests for group, task, sprint, and routing slices.
- [ ] Add idempotency strategy for repeated Telegram actions.
- [ ] Add tests for sprint math, weights, and ownership changes.
- [x] Add balance transfer tests.
- [ ] Add observability hooks: structured logging, request IDs, and job logs.

## Legacy Coverage
- [ ] Replace all handler-embedded ORM logic from [`UnitKeeperBot/handlers`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/UnitKeeperBot/handlers)
- [ ] Replace sprint scheduler from [`UnitKeeperBot/sprint_results.py`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/UnitKeeperBot/sprint_results.py)
- [ ] Keep behavior parity first, then improve internals

## Deferred For Later
- [ ] Benefit shop.
- [ ] Calendar integration.
- [ ] External analytics or BI exports.
