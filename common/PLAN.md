# Common Plan

## Goal
- Build the shared persistence layer used by backend and bot.
- Keep database schema, migrations, and low-level data access in one place.

## Scope
- SQLAlchemy models and metadata.
- Alembic migrations.
- Session management and DB wiring.
- Shared enums, value objects, and persistence-facing DTOs if needed.

## Phase 1: Package Skeleton
- [ ] Create Python package structure for shared DB code.
- [ ] Introduce configuration for database URL and engine settings.
- [ ] Add async session factory and transaction helpers.
- [ ] Set naming conventions for metadata and migrations.

## Phase 2: Domain Schema
- [ ] Rebuild entities for users, groups, memberships, tasks, task logs, balances, and sprint runs.
- [ ] Normalize legacy weak spots where needed without losing behavior.
- [ ] Decide which Telegram profile fields are cached locally and which remain external.
- [ ] Model ownership, workload weights, and task status explicitly.
- [ ] Decide whether sprint snapshots or result tables are needed instead of recalculating everything from raw logs.

## Phase 3: Migrations
- [ ] Initialize Alembic.
- [ ] Create baseline migration for the new schema.
- [ ] Add seed or bootstrap strategy for local development.
- [ ] Define migration policy for future product iterations.

## Phase 4: Shared Access Layer
- [ ] Add repositories or query services for backend use cases.
- [ ] Add Unit of Work boundary used by backend and background jobs.
- [ ] Expose read models needed by the thin bot without leaking business logic into bot code.
- [ ] Prepare import path conventions so backend and bot share the package cleanly.

## Migration Tasks From Legacy
- [ ] Map `Group.weights` JSON to the new representation.
- [ ] Preserve soft-delete semantics for tasks.
- [ ] Preserve pending/completed log statuses.
- [ ] Preserve per-user balances and group-level economics.
- [ ] Fix legacy inconsistency around `group_balance` versus `balance`.
- [ ] Decide how to represent sprint periods and scheduler bookkeeping explicitly.

## Non-Goals
- [ ] No HTTP endpoints here.
- [ ] No Telegram handler logic here.
- [ ] No frontend-specific code here.
