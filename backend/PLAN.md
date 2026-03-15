# Backend Plan

## Goal
- Move all business rules into a FastAPI service.
- Backend becomes the only place that knows product logic.

## Scope
- FastAPI app, Dishka DI, business services, auth, scheduler orchestration, and integrations.

## Phase 1: Service Foundation
- [ ] Bootstrap FastAPI application structure.
- [ ] Wire Dishka containers for config, DB sessions, repositories, services, and background jobs.
- [ ] Add health endpoint and local developer run path.
- [ ] Define public API shape before implementing screens.

## Phase 2: Auth And Session Context
- [ ] Verify Telegram Mini App init data on the backend.
- [ ] Resolve or create local user records from Telegram identity.
- [ ] Provide current-user and current-group context dependencies.
- [ ] Decide whether the bot also authenticates through service credentials or internal transport.

## Phase 3: Core Use Cases
- [ ] Create group.
- [ ] Join group.
- [ ] Leave group with owner handover rules.
- [ ] Read group info and members.
- [ ] Update group settings.
- [ ] Create, bulk import, edit, soft-delete, and list tasks.
- [ ] Compute remaining task executions within the current sprint.
- [ ] Mark task completion.
- [ ] Approve or reject task completion.
- [ ] Read sprint progress and current results.
- [ ] Read balance and transfer units.

## Phase 4: Scheduling And Notifications
- [ ] Rebuild sprint closing logic as backend jobs.
- [ ] Store scheduler-safe bookkeeping to avoid duplicate sprint closure.
- [ ] Produce notification events for the bot.
- [ ] Produce deep links for miniapp navigation from notifications.
- [ ] Add reminder jobs for pending confirmations and sprint deadlines.

## Phase 5: Reliability
- [ ] Add validation and business error taxonomy.
- [ ] Add idempotency strategy for repeated Telegram actions.
- [ ] Add tests for sprint math, weights, ownership changes, and balance transfers.
- [ ] Add observability hooks: structured logging, request IDs, and job logs.

## Legacy Coverage
- [ ] Replace all handler-embedded ORM logic from [`UnitKeeperBot/handlers`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/UnitKeeperBot/handlers)
- [ ] Replace sprint scheduler from [`UnitKeeperBot/sprint_results.py`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/UnitKeeperBot/sprint_results.py)
- [ ] Keep behavior parity first, then improve internals

## Deferred For Later
- [ ] Benefit shop.
- [ ] Calendar integration.
- [ ] External analytics or BI exports.
