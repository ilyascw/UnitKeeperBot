# Common Plan

## Goal
- Build the shared persistence layer used by backend and bot.
- Keep database schema, migrations, and low-level data access in one place.

## Scope
- SQLAlchemy models and metadata.
- Alembic migrations.
- Session management and DB wiring.
- Shared enums, value objects, and persistence-facing DTOs if needed.

## Current Status
- [x] Shared package `unitkeeper-common` with import surface under `src/db`.
- [x] PostgreSQL settings, async engine, sessionmaker, and transaction helpers.
- [x] Naming conventions for metadata and Alembic.
- [x] Initial normalized UnitKeeper schema and baseline migration.
- [x] Documentation for schema choices and legacy deviations.
- [ ] Seed/bootstrap dataset for local development.
- [x] Migration smoke tests for a fresh database upgrade.
- [ ] Forward migration policy for the next iterations.
- [x] Persistence primitives for notification outbox and idempotency.
- [ ] Cutover support.

## Phase 1: Package Skeleton
- [x] Create Python package structure for shared DB code.
- [x] Introduce configuration for database URL and engine settings.
- [x] Add async session factory and transaction helpers.
- [x] Set naming conventions for metadata and migrations.

## Phase 2: Domain Schema
- [x] Rebuild entities for users, groups, memberships, tasks, task logs, balances, and sprint runs.
- [x] Normalize legacy weak spots where needed without losing behavior.
- [x] Decide which Telegram profile fields are cached locally and which remain external.
- [x] Model ownership, workload weights, and task status explicitly.
- [x] Decide whether sprint snapshots or result tables are needed instead of recalculating everything from raw logs.

## Phase 3: Migrations
- [x] Initialize Alembic.
- [x] Create baseline migration for the new schema.
- [ ] Add seed or bootstrap strategy for local development.
- [ ] Define migration policy for future product iterations.

## Phase 4: Shared Access Layer
- [x] Prepare import path conventions so backend and bot share the package cleanly.
- [ ] Decide which shared repository/query helpers belong in `common` versus backend infrastructure.
- [x] Expose storage primitives for bot notification delivery and idempotent external actions.
- [x] Add migration and schema smoke tests around the shared package surface.

## Migration Tasks From Legacy
- [x] Map `Group.weights` JSON to the new representation.
- [x] Preserve soft-delete semantics for tasks.
- [x] Preserve pending/completed log statuses.
- [x] Preserve per-user balances and group-level economics.
- [x] Fix legacy inconsistency around `group_balance` versus `balance`.
- [x] Decide how to represent sprint periods and scheduler bookkeeping explicitly.

## Non-Goals
- [ ] No HTTP endpoints here.
- [ ] No Telegram handler logic here.
- [ ] No frontend-specific code here.
