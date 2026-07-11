# Legacy Data Bootstrap

Legacy bot data uses the schema captured by Alembic revision `20260315_0000`:

- `groups`: `id`, `name`, `password`, `start_day`, `sprint_duration`, `owner_id`, `group_balance`, `weights`
- `users`: `id`, `group_id`
- `tasks`: `id`, `group_id`, `title`, `frequency`, `cost`, `status`
- `logs`: `id`, `group_id`, `user_id`, `task_id`, `status`, `timestamp`
- `balances`: `id`, `user_id`, `group_id`, `balance`

Revision `20260315_0001` migrates that legacy schema into the current backend schema.

## Data-Only Dump

Use this when the dump contains only `INSERT`/`COPY` data for the legacy tables.

```bash
cd common
make up
PYTHONPATH=src .venv/bin/python -m alembic upgrade 20260315_0000
psql "postgresql://unitkeeper:unitkeeper@127.0.0.1:5432/unitkeeper_common" -f /path/to/legacy-data.sql
PYTHONPATH=src .venv/bin/python -m alembic upgrade head
```

## Full Schema Dump

Use this when the dump creates the old `groups`, `users`, `tasks`, `logs`, and `balances`
tables itself.

```bash
cd common
make up
psql "postgresql://unitkeeper:unitkeeper@127.0.0.1:5432/unitkeeper_common" -f /path/to/legacy-full.sql
PYTHONPATH=src .venv/bin/python -m alembic stamp 20260315_0000
PYTHONPATH=src .venv/bin/python -m alembic upgrade head
```

## Migration Mapping

- `groups.password` -> `groups.join_secret`
- `groups.start_day` -> `groups.sprint_start_weekday`
- `groups.sprint_duration` -> `groups.sprint_duration_days`
- `groups.owner_id` -> `groups.owner_user_id`
- `groups.group_balance` -> `groups.balance`
- `users.group_id` -> active `group_memberships`
- `groups.weights` -> `group_member_weights`
- `tasks.frequency` -> `tasks.frequency_per_sprint`
- `tasks.cost` -> `tasks.unit_cost`
- `tasks.status = false` -> `tasks.deleted_at`
- `logs` -> `task_logs`
- `balances.balance` -> `balances.current_balance`
- non-zero legacy balances also create opening `balance_transactions`

After `upgrade head`, run the backend against the same PostgreSQL database URL.
