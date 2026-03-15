# Task For Subagent: Raise `common` Layer

## Context
- Repository root: `/Users/ilaskvorcov/Desktop/дело/unitkeeper`
- Legacy source of truth: [`UnitKeeperBot`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/UnitKeeperBot)
- Functional migration map: [`docs/legacy-functionality.md`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/docs/legacy-functionality.md)
- Target architecture rules: [`AGENTS.md`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/AGENTS.md)
- Folder to work in: [`common`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/common)

## What You Are Building
You need to turn the current template in `common/` into the shared persistence layer for UnitKeeper.

This layer must become the single source for:
- SQLAlchemy models
- Alembic migrations
- DB settings and engine/session wiring
- shared enums and persistence primitives used later by backend and bot

This layer must **not** contain:
- FastAPI endpoints
- Telegram handlers
- business use case orchestration
- miniapp/frontend code

## Important Starting Point
The current `common/` template is not aligned with UnitKeeper:
- package metadata still references another project (`eventmatch-db`)
- current models/enums describe чужую предметную область (`events`, `employees`, `plans`, etc.)
- current codebase includes stale `__pycache__` artifacts inside `src/db`

Do not adapt that foreign domain model incrementally. Replace it with a clean UnitKeeper-oriented shared DB package.

## Product Constraints From Legacy
Preserve the product behavior described in [`docs/legacy-functionality.md`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/docs/legacy-functionality.md), especially:
- users exist independently from a group
- groups have owner, sprint start day, sprint duration, and workload weights
- tasks belong to a group and support soft delete
- task execution logs support at least `pending` and `completed`
- balances exist per user per group
- there is a group-level economics concept
- sprint closing requires enough data to compute plan/fact and send reports

Do not blindly port known legacy bugs. In particular:
- do not keep the `group_balance` vs `balance` inconsistency
- do not keep weak ad hoc JSON fields if a normalized structure is clearly better

## Primary Goal
Deliver a first solid version of the `common` layer that backend and bot can safely build on.

## Required Outcome

### 1. Clean package and infra
Make `common/` a clean reusable Python package for UnitKeeper:
- package name and metadata must match UnitKeeper, not EventMatch
- remove or replace irrelevant models/enums/types from the template
- remove committed `__pycache__` files from `common/src/db`
- keep Docker, Alembic, and local dev flows working

### 2. Define the target schema
Design and implement the first UnitKeeper schema in SQLAlchemy 2 style.

At minimum it must cover these concepts:
- user
- group
- group membership or equivalent relation
- group ownership
- sprint configuration
- workload weights
- task
- task completion log / task execution log
- balance
- some explicit representation for sprint closing or sprint period bookkeeping if needed

You may choose normalized tables instead of copying legacy structure one-to-one, but the result must still support all legacy flows.

### 3. Add migrations
Set up the initial Alembic baseline for the UnitKeeper schema:
- ensure autogenerate works
- create initial migration
- make local upgrade path straightforward

### 4. Expose shared DB wiring
Provide shared DB primitives that backend and bot can reuse:
- settings
- engine
- async session maker
- base metadata
- optional helper for transaction/session dependency

### 5. Document decisions
Document the resulting schema and key deviations from legacy:
- what was preserved exactly
- what was normalized
- what was intentionally deferred

## Expected Deliverables

### Code deliverables
- updated [`common/pyproject.toml`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/common/pyproject.toml)
- cleaned and relevant code under [`common/src/db`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/common/src/db)
- working Alembic config under [`common/alembic`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/common/alembic)
- initial migration in `common/alembic/versions/`
- if necessary, adjusted Docker and Make targets in [`common/Makefile`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/common/Makefile), [`common/docker-compose.yml`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/common/docker-compose.yml), [`common/docker-compose.dev.yml`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/common/docker-compose.dev.yml)

### Documentation deliverables
- update [`common/README.md`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/common/README.md) so it reflects UnitKeeper rather than the template
- add a short schema/design note, either inside `common/README.md` or as a dedicated file such as `common/ARCHITECTURE.md`

## Suggested Domain Direction
You do not have to follow this exact schema, but the design should likely converge around something close to this:

### Core entities
- `users`
  - telegram user id
  - optional cached Telegram profile fields
  - timestamps

- `groups`
  - name
  - join secret / password
  - owner user id
  - sprint start weekday
  - sprint duration days
  - timezone
  - group-level balance or equivalent aggregate field
  - timestamps

- `group_memberships`
  - user id
  - group id
  - role or ownership marker if needed
  - active membership flag or leave timestamp

- `group_member_weights`
  - membership or `(group_id, user_id)`
  - workload percentage

- `tasks`
  - group id
  - title
  - frequency per sprint
  - unit cost
  - active / soft-delete flag

- `task_logs`
  - group id
  - task id
  - performer user id
  - status
  - created at / decided at
  - approver user id if relevant
  - rejection reason if relevant

- `balances`
  - group id
  - user id
  - current balance

### Optional but recommended entities
- `sprint_runs`
  - group id
  - period start
  - period end
  - status
  - closed at

- `balance_transactions`
  - group id
  - sender user id nullable
  - recipient user id nullable
  - amount
  - reason / type
  - sprint run id nullable

If you introduce `balance_transactions`, explain the tradeoff and whether `balances` are now derived or still stored denormalized.

## Decision Rules
- Prefer normalized schema where it removes obvious legacy pain.
- Preserve behavior needed for migration, not accidental implementation defects.
- Prefer explicit tables over JSON blobs when the data has relational meaning.
- Keep the design small. This is a v1 common layer, not the final enterprise data platform.
- Avoid speculative entities for benefit shop, calendar sync, or analytics unless they are necessary now.

## Concrete Work Plan

### Step 1. Audit current template
- inspect current models/enums/settings/alembic in `common/`
- identify what can be reused structurally and what must be replaced
- keep only infrastructure pieces that are genuinely useful for UnitKeeper

### Step 2. Propose target schema
- derive the schema from legacy functionality in `docs/legacy-functionality.md`
- make a concise design decision on memberships, weights, task logs, and sprint bookkeeping
- avoid overengineering

### Step 3. Implement models and enums
- replace foreign template entities with UnitKeeper entities
- ensure naming is clean and consistent
- ensure SQLAlchemy 2 typing is sane
- include indexes and uniqueness constraints where clearly needed

### Step 4. Wire settings and DB helpers
- keep `pydantic-settings`
- expose a clean `DATABASE_URL`
- expose engine and async sessionmaker
- keep the code importable by future backend and bot packages

### Step 5. Fix Alembic
- ensure metadata import is correct
- ensure migration env uses the new models
- generate and verify the initial migration

### Step 6. Fix local infra
- confirm docker compose and Make targets still make sense for local PostgreSQL usage
- adjust image/container naming if the template still references the old project

### Step 7. Update docs
- replace template README content
- explain how to run Postgres, how to apply migrations, and what entities now exist

## Acceptance Criteria
The task is complete only if all of the following are true:

- `common/` no longer contains foreign EventMatch domain models as active code
- package metadata no longer references `eventmatch-db`
- committed `__pycache__` files are removed from source tree
- UnitKeeper entities needed for migration are represented in SQLAlchemy models
- Alembic can see metadata and has an initial migration
- `common/README.md` describes the real UnitKeeper common layer
- The resulting schema can support these legacy scenarios:
  - create group
  - join group
  - leave group / owner handover
  - manage tasks
  - mark task done
  - approve/reject task completion
  - compute current sprint progress
  - store balances
  - close sprint and persist its effects

## Non-Goals
- Do not build backend services or repositories beyond what is strictly needed for shared DB infrastructure.
- Do not implement FastAPI.
- Do not implement the bot.
- Do not build the miniapp.
- Do not migrate runtime business logic from handlers yet.

## Output Format Required From You
When you finish, provide:

1. A short summary of what changed.
2. The final schema overview.
3. Explicit list of legacy mismatches you resolved intentionally.
4. Any open questions or risky assumptions.
5. What commands you ran to verify the result.

## Useful Local References
- [`common/PLAN.md`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/common/PLAN.md)
- [`common/README.md`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/common/README.md)
- [`common/src/db/database.py`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/common/src/db/database.py)
- [`common/src/db/models.py`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/common/src/db/models.py)
- [`common/src/db/enums.py`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/common/src/db/enums.py)
- [`common/src/db/settings.py`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/common/src/db/settings.py)
- [`common/alembic/env.py`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/common/alembic/env.py)

## Final Instruction
Bias toward a clean, minimal, defensible schema that unblocks `backend` and `bot` immediately. If you have to choose between preserving a legacy storage quirk and creating a clean migration-ready foundation, choose the clean foundation and document the deviation.
