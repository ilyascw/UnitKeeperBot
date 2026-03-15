# Task For Backend Subagent: Build First Critical Backend Slice

## Context
- Repository root: `/Users/ilaskvorcov/Desktop/дело/unitkeeper`
- Architecture rules: [`AGENTS.md`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/AGENTS.md)
- Legacy behavior map: [`docs/legacy-functionality.md`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/docs/legacy-functionality.md)
- Shared persistence layer: [`common`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/common)
- Common schema notes: [`common/ARCHITECTURE.md`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/common/ARCHITECTURE.md)
- Current backend plan: [`backend/PLAN.md`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/backend/PLAN.md)

## What You Are Building
You are building the first serious backend slice for UnitKeeper.

This backend must become the only place that owns business rules for:
- Telegram Mini App authentication
- current user and current group resolution
- group lifecycle
- tasks lifecycle
- task completion and approval flow
- sprint progress
- sprint closing

This backend must be production-minded from the start:
- FastAPI
- SQLAlchemy async
- Dishka DI
- clear service boundaries
- tests for business logic and HTTP contracts
- predictable error model

## Scope For This Task
Implement only the first critical product slice:

1. auth through Telegram Mini App init data
2. current user / current group resolution
3. create / join / leave group
4. tasks CRUD
5. mark done / approve / reject
6. temp results / sprint close

Do not expand scope into “everything backend should eventually do”. This is an MVP-grade but architecturally sane slice.

## Core Architectural Rules

### Required patterns
- Use a clear application layer with use cases or services.
- Keep HTTP routers thin.
- Keep ORM queries out of routers.
- Use repositories only for persistence concerns, not for business orchestration.
- Use a Unit of Work or equivalent transaction boundary for write use cases.
- Use explicit DTOs / schemas for API I/O.
- Use domain/application exceptions and map them to HTTP responses centrally.
- Use DI through Dishka consistently instead of ad hoc global singletons.

### Explicit anti-patterns to avoid
- no business logic inside FastAPI route functions
- no direct session commits from controllers
- no god-service that knows everything
- no “repository as service layer” style
- no duplicated sprint math in multiple modules
- no leaking SQLAlchemy models directly as public API responses
- no hidden side effects inside simple read endpoints

## Expected Backend Shape
You may choose exact filenames, but the resulting structure should be close to this:

```text
backend/
├── src/unitkeeper_backend/
│   ├── api/
│   │   ├── routers/
│   │   ├── schemas/
│   │   └── dependencies/
│   ├── application/
│   │   ├── auth/
│   │   ├── groups/
│   │   ├── tasks/
│   │   ├── sprints/
│   │   └── balances/
│   ├── domain/
│   │   ├── errors.py
│   │   └── services/
│   ├── infrastructure/
│   │   ├── db/
│   │   ├── auth/
│   │   ├── repositories/
│   │   ├── uow/
│   │   └── jobs/
│   ├── config.py
│   ├── di.py
│   └── main.py
└── tests/
    ├── unit/
    ├── integration/
    └── api/
```

The exact layout may differ, but the separation of concerns must stay this clean.

## Product Behavior To Preserve
Use [`docs/legacy-functionality.md`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/docs/legacy-functionality.md) as product truth.

Especially preserve:
- user can exist before joining a group
- user can have only one active group membership at a time
- group has owner, sprint start weekday, sprint duration, weights
- tasks belong to a group and can be soft-deleted
- task completion flow uses pending approval for multi-member groups
- single-member group auto-completes task execution
- approvals must respect task frequency limit within the sprint
- rejection carries a reason
- temp results show plan vs fact for current sprint
- sprint close mutates balances and stores results

Do not preserve known legacy bugs as behavior requirements.

## Use Cases To Implement

### 1. Telegram auth
Implement backend authentication for Telegram Mini App init data.

Required behavior:
- verify Telegram init data correctly
- extract Telegram user identity
- create local user if missing
- update cached Telegram profile fields if changed
- issue backend session representation or signed token for subsequent API calls

Expected result:
- backend endpoints can resolve authenticated user without trusting plain client-sent user ids

### 2. Current user / current group context
Implement reusable context resolution for:
- current authenticated user
- current active membership if it exists
- current active group if it exists

This must be reusable from application services and routers without duplicated query logic.

### 3. Create group
Required behavior:
- user without active group can create a group
- validate unique group name
- validate join secret / password
- validate sprint duration is positive and divisible by 7
- create group
- create active membership for owner
- initialize owner weight to 100
- initialize personal balance
- set owner as current group owner

### 4. Join group
Required behavior:
- user without active group can join
- joining is based on group name plus join secret semantics unless you propose and document another temporary input contract
- create active membership
- initialize balance if missing
- rebalance weights across active members according to current legacy intent

If you intentionally improve this rule, document it very explicitly.

### 5. Leave group
Required behavior:
- user can leave active group
- active membership becomes inactive rather than disappearing
- membership weights are recalculated or adjusted consistently
- owner handover is handled

Important:
- if current `common` schema makes “group without owner” impossible, backend must define a clean policy for the final member leaving the group
- do not leave the data in an impossible or dangling state

### 6. Tasks CRUD
Required behavior:
- create task
- list active tasks in current group
- get task detail
- update task title/frequency/cost
- soft-delete task

Validation:
- title required
- frequency positive integer
- unit cost non-negative

For this task, spreadsheet import can be deferred unless it is trivial to plug in cleanly.

### 7. Mark task done
Required behavior:
- user selects a task from current group
- system checks remaining executions within the current sprint
- if group has one active member, complete immediately
- otherwise create pending task log
- return enough response data for bot and future miniapp approval UX

### 8. Approve task
Required behavior:
- another active group member can approve pending task log
- performer cannot self-approve in multi-member flow unless you explicitly choose that and document it
- system enforces frequency cap inside the current sprint
- successful approval finalizes log state and timestamps
- related balance movement or later settlement dependency must remain coherent

### 9. Reject task
Required behavior:
- active group member can reject pending task log
- rejection reason is required
- task log becomes rejected with audit fields filled

### 10. Temp results
Required behavior:
- resolve current sprint window for group
- compute planned units for current user from active tasks and current weight
- compute completed units from completed task logs in sprint window
- compute progress percent
- return completed task breakdown

### 11. Sprint close
Required behavior:
- close a sprint for a group exactly once
- persist sprint run and per-member results
- compute plan, fact, bonus, balance deltas
- update balances
- write balance transactions

Important:
- make this logic idempotent or explicitly protected against duplicate closure for the same period

## Suggested HTTP Surface
You may improve naming, but the first slice should expose something close to this:

### Auth
- `POST /auth/telegram`
  - verifies init data
  - returns session/token + current user summary

### Me / context
- `GET /me`
- `GET /me/group`

### Groups
- `POST /groups`
- `POST /groups/join`
- `POST /groups/leave`
- `GET /groups/current`

### Tasks
- `GET /tasks`
- `POST /tasks`
- `GET /tasks/{task_id}`
- `PATCH /tasks/{task_id}`
- `DELETE /tasks/{task_id}`
- `POST /tasks/{task_id}/complete`

### Task approvals
- `POST /task-logs/{task_log_id}/approve`
- `POST /task-logs/{task_log_id}/reject`

### Sprint results
- `GET /sprints/current/results`
- `POST /sprints/current/close`

If you rename endpoints, keep them coherent and document the final shape.

## Error Model Requirements
Define explicit application errors, for example:
- authentication failed
- no active group
- already in a group
- group not found
- invalid join secret
- group name already taken
- task not found
- task not in current group
- task frequency limit exceeded
- task log not pending
- approval forbidden
- rejection reason required
- sprint already closed

Map them to stable HTTP responses in one place.

Avoid returning raw SQLAlchemy or generic 500-style validation noise for known business cases.

## Good Defaults “Out Of The Box”
The implementation must feel sane from day one.

This includes:
- config through `pydantic-settings`
- one app factory or clean startup entrypoint
- structured logging
- central exception handling
- request-scoped DI
- transactional write use cases
- clear typing
- time handling in UTC internally
- no hidden implicit autocommits
- separation between API schemas and DB models

## Testing Requirements

### Mandatory test layers

#### 1. Unit tests for business logic
Cover at least:
- create group validation
- join group validation
- leave group ownership handover policy
- task creation/update/delete validation
- mark done single-member auto-complete
- mark done multi-member pending flow
- approve with remaining limit
- reject with reason required
- temp results math
- sprint close calculations
- sprint close idempotency / duplicate protection

#### 2. Integration tests for persistence behavior
Cover at least:
- repositories / UoW behavior against a real test database
- membership activation/deactivation
- weight storage and retrieval
- task soft delete semantics
- task log status transitions
- balance and balance transaction persistence
- sprint run persistence

#### 3. API tests
Cover at least:
- auth endpoint happy path and invalid init data
- protected endpoint access
- create group
- join group
- leave group
- tasks CRUD
- mark complete / approve / reject
- current sprint results
- sprint close

### Test quality rules
- no fake tests that only assert status code 200 without checking state
- use factories / fixtures instead of noisy inline setup
- isolate time-sensitive logic cleanly
- make sprint math deterministic in tests
- prefer one clear assertion chain per behavior rather than giant snapshot blobs

## DoD: Definition Of Done
The backend task is done only if all points below are true.

### Architecture DoD
- backend has a clean app structure
- routes are thin and delegate to application layer
- write operations are transactionally bounded
- DI is wired through Dishka
- shared persistence comes from `common`, not local duplicate models
- public API does not expose raw ORM entities

### Product DoD
- Telegram auth works for backend session bootstrap
- current user and current group are resolvable
- create/join/leave group works against the new schema
- tasks CRUD works
- mark done / approve / reject works
- temp results works
- sprint close works and persists results safely

### Quality DoD
- unit tests exist for all critical business cases
- integration tests cover core persistence flows
- API tests cover main endpoints
- no failing tests
- code is typed and readable
- key assumptions and intentional deviations are documented

### Operational DoD
- local startup instructions exist
- test run instructions exist
- env configuration is documented
- backend can run against the existing `common` DB setup

## Non-Goals
- do not build the bot in this task
- do not build the miniapp in this task
- do not implement the entire eventual feature set
- do not add benefit shop, calendar, analytics, or recommendation systems
- do not bury notification delivery inside backend HTTP handlers; only prepare the backend side of the flow

## Recommended Work Order

1. Bootstrap backend package and config
2. Wire Dishka and DB dependencies
3. Implement auth and current-context resolution
4. Implement group use cases
5. Implement task CRUD
6. Implement completion / approve / reject flow
7. Implement temp results
8. Implement sprint close
9. Add API tests and integration tests
10. Harden error handling and documentation

## Expected Deliverables

### Code
- backend package structure
- FastAPI app
- Dishka wiring
- application services / use cases
- repositories / UoW
- HTTP routers and schemas
- tests

### Docs
- backend README with run/test instructions
- short architecture note if the folder layout is not self-explanatory
- explicit note about sprint-close duplicate protection strategy

## Output Format Required From You
When you finish, provide:

1. Short summary of implemented backend slice.
2. Final package structure.
3. Final endpoint list.
4. Business assumptions and intentional deviations from legacy.
5. Test coverage summary.
6. Commands you ran for verification.
7. Remaining gaps that should be handled by bot or miniapp later.

## Final Instruction
Bias toward a backend that is boring in the best sense: explicit boundaries, predictable flows, testable business logic, no framework magic in the core. Build the first slice so that bot and miniapp can become thin clients over it rather than competing sources of truth.
