# UnitKeeper Common

`common/` is the shared persistence layer for UnitKeeper. It is the single source for:

- SQLAlchemy 2 models
- Alembic migrations
- PostgreSQL settings and async session wiring
- shared enums and persistence primitives reused by backend and bot

Business rules, Telegram handlers, FastAPI endpoints, and Mini App UI code do not belong here.

## Quick Start

Run everything from `common/`.

```bash
cp .env.example .env
uv pip install .
make up
make migrate
```

The default `.env.example` values point to a local PostgreSQL instance on `127.0.0.1:5432`.

## Main Commands

| Command | Description |
| --- | --- |
| `make up` | Start local PostgreSQL via Docker Compose |
| `make down` | Stop local PostgreSQL |
| `make migrate` | Apply all Alembic migrations |
| `make revision m="..."` | Create a new migration with autogenerate |

## Package Surface

The package is installed as `unitkeeper-common`, while the import path remains `db`:

```python
from db import Group, Task, User, async_session_maker, settings
```

Core shared primitives live under `src/db`:

- `models.py`: schema entities
- `enums.py`: shared enums
- `database.py`: metadata, engine, sessionmaker, session helpers
- `settings.py`: DB configuration

## Schema Overview

The v1 schema covers:

- `users`: Telegram users with optional cached profile fields
- `groups`: group configuration, owner, sprint settings, and group-level balance
- `group_memberships`: membership history with at most one active membership per user
- `group_member_weights`: normalized workload weights per membership
- `tasks`: group tasks with soft delete via `deleted_at`
- `task_logs`: pending/completed/rejected execution logs with approval metadata
- `balances`: current per-user balance inside a group
- `balance_transactions`: auditable signed ledger entries for transfers and sprint settlements
- `sprint_runs`: sprint periods with aggregate plan/fact totals
- `sprint_member_results`: stored per-user sprint outcomes for reports and history

More detail is captured in `ARCHITECTURE.md`.

## Migration Workflow

1. Update the SQLAlchemy models in `src/db/models.py`.
2. Generate a migration: `make revision m="describe change"`.
3. Review the generated file in `alembic/versions/`.
4. Apply it locally with `make migrate`.

## Legacy Data Bootstrap

Legacy bot dumps should be restored at Alembic revision `20260315_0000`, then upgraded to
`head` to transform data into the backend v1 schema. See
[`docs/common/legacy-data-bootstrap.md`](../docs/common/legacy-data-bootstrap.md).
