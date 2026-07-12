# UnitKeeper

## Intent
- This repository is the new wave of UnitKeeper: Telegram Mini App as the main UI, a thin Telegram bot for notifications, and a FastAPI backend with SQLAlchemy, Dishka, and Alembic.
- The project is expected to run as several containers.

## Source Of Truth
- Until migration is complete, [`UnitKeeperBot`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/UnitKeeperBot) is the source of truth for legacy behavior.
- If a document conflicts with legacy code, legacy code wins unless we explicitly decide to change product behavior.
- We preserve product intent, not accidental implementation bugs.

## Target Structure
- [`miniapp`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/miniapp): native Telegram Mini App with Telegram UI Kit.
- [`common`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/common): shared database layer for backend and bot, including SQLAlchemy models, Alembic migrations, and DB integration code.
- [`backend`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/backend): FastAPI app with business use cases, API contracts, auth, schedulers, and integrations.
- [`bot`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/bot): thin Telegram bot for notifications, deep links, and minimal fallback flows.
- [`docs`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/docs): migration notes and legacy functional artifacts.

## Running the full stack locally (backend + bot in Docker, miniapp via Vite + ngrok)

Prereqs: `docker`, `uv`, `npm`, `ngrok` installed. Do these steps in order.

1. **Free port 5432 if needed.** `docker ps` — another project may already have a container named `db` bound to 5432 (seen: an `eventmatch` pgvector container). `docker stop <name>` it before continuing.
2. **Start Postgres:** `cd common && make up` (creates `common-db-1` on the `common_default` docker network, reading creds from `common/.env`: `POSTGRES_USER=app_user`, `POSTGRES_PASSWORD=secret`, `POSTGRES_DB=uk_db`).
3. **Run migrations** (from `common/`): `PYTHONPATH=src uv run alembic upgrade head`.
4. **Fix `backend/.env`'s `DATABASE_URL`** to match the real DB creds from step 2 — it does *not* default to matching `common/.env` and has drifted before:
   - in-container (backend running via docker compose, step 6): `postgresql+asyncpg://app_user:secret@db:5432/uk_db`
   - running backend outside Docker: `postgresql+asyncpg://app_user:secret@127.0.0.1:5432/uk_db`
5. **Set `bot/.env`** per `.env.example`: `UNITKEEPER_BOT_TOKEN`, `UNITKEEPER_BACKEND_BASE_URL=http://backend:8000/api/v1`, `UNITKEEPER_INTERNAL_BOT_SECRET` (must match `backend/.env`'s `INTERNAL_BOT_SECRET`), `UNITKEEPER_MINIAPP_URL` (placeholder until step 8).
6. **Build and start backend + bot containers** (from repo root): `docker compose build backend bot && docker compose up -d backend bot`. Uses root `docker-compose.yml`, which attaches both services to the external `common_default` network so they can reach `db` and each other by hostname.
7. **Start the miniapp dev server** (not containerized): `cd miniapp && npm install && npm run dev` (port 5173). `vite.config.ts` already proxies `/api` to `http://127.0.0.1:8000` and allowlists `.ngrok-free.dev` hosts.
8. **Expose it over HTTPS:** `ngrok http 5173`. Copy the resulting `https://*.ngrok-free.dev` URL into `bot/.env`'s `MINIAPP_URL`, then `docker compose up -d bot` to restart the bot with the new Web App URL.
9. **(Optional) seed legacy CSV data** from `data/*.csv` into the DB: `cd backend && PYTHONPATH=src:../common/src uv run python scripts/import_legacy_csv.py --database-url "postgresql+asyncpg://app_user:secret@127.0.0.1:5432/uk_db"`. Ran cleanly against the current head migration; prints per-user Swagger bearer tokens at the end.

### Notes / gotchas discovered while wiring this up

- `backend` depends on the local `unitkeeper-common` package but `backend/pyproject.toml` had no `[tool.uv.sources]` entry, so `uv sync` failed with "not found in package registry". Fixed by adding:
  ```toml
  [tool.uv.sources]
  unitkeeper-common = { path = "../common", editable = true }
  ```
- `bot/src/unitkeeper_bot/config.py`'s `Settings` was missing `env_prefix="UNITKEEPER_"`, so the un-prefixed env vars (`BOT_TOKEN`, etc) were required even though `bot/README.md` and `bot/.env.example` document `UNITKEEPER_`-prefixed names. Fixed by adding `env_prefix="UNITKEEPER_"` to `model_config` — `bot/.env` now matches `.env.example` as documented.
- There was no root-level `docker-compose.yml` or Dockerfiles for `backend`/`bot` (only `common` had Docker wiring, for the DB). Added `backend/Dockerfile`, `bot/Dockerfile` (prod deps only, `pip install -e .`, no dev extras) and a root `docker-compose.yml`.

## Balance ledger (double-entry)

`balance_transactions` is an append-only double-entry ledger, not just an audit log: every logical operation (transfer, sprint settlement) writes one or more rows sharing a `transaction_group_id`, and the `amount_delta` of every row in a group must sum to zero. `account_type` distinguishes `user` legs (post to a member's balance, `user_id` required) from `group_pool` legs (the counter-leg for sprint settlements, which have no single counterparty user — `user_id` must be NULL). This is enforced by a DB CHECK constraint (`balance_transactions_account_type_user_id`). `Balance.current_balance` remains a mutated running-total cache; it must always equal the sum of that user's ledger rows — there's no reconciliation job yet, that's a gap if this drifts.

Sprint settlement (`SprintService.close_current_sprint`) writes one `GROUP_POOL` leg for the total payout plus one `USER` leg per member with a nonzero delta, all sharing one `transaction_group_id`. Manual transfers (`BalanceService.transfer`) write a sender/recipient pair sharing one `transaction_group_id`. The legacy-CSV opening-balance import (`_migrate_legacy_data` in `20260315_0001_initial_unitkeeper_schema.py`) intentionally writes single-legged `manual_adjustment` rows — that's an external funding injection (analogous to a bank's opening deposit), not a bug.

Since this schema had no data to preserve yet (migration decided with the user 2026-07-12), the ledger columns (`account_type`, `transaction_group_id`) were added by editing the existing `20260315_0001_initial_unitkeeper_schema.py` migration in place rather than stacking a new migration — if this schema is ever shared/deployed elsewhere, that approach stops being safe and a new migration must be used instead.

## Working Rules
- New business logic goes to backend services, not to bot handlers or miniapp UI code.
- Bot and miniapp should depend on backend contracts; direct business logic duplication is not allowed.
- Shared DB models and migrations live in `common`.
- Each migrated feature should be traceable back to the legacy artifact in [`docs/legacy-functionality.md`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/docs/legacy-functionality.md).
- Use ruff, mypy, uv, tests
- Python services must use `pyproject.toml` as the project entrypoint for dependencies and tooling; do not add ad hoc dependency files when `pyproject.toml` is appropriate.
- Use `uv` to create and manage the virtual environment for the service you are working on.
- The virtual environment must live inside the working service directory, not at repo root. Example: when working on [`backend`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/backend), create and activate [`backend/.venv`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/backend/.venv).

## Branching

- `main` is production. It only moves via a merge from `dev` once the migration (or a batch of it) is judged production-ready — never commit or merge feature work directly into `main`.
- `dev` is the integration branch for the whole migration. All issue work branches off `dev` and merges back into `dev` via PR.
- Issue branches are named `<area>/issue-NN-slug`, e.g. `backend/issue-04-balances`, `miniapp/issue-05-transfer-screen`, `bot/issue-02-notifications`. `<area>` is the top-level directory the work is mostly in (`backend`, `bot`, `common`, `miniapp`); cross-cutting work picks whichever area is primary.
  - Do not use a `dev/...` prefix for these branches — git refs can't have both a branch named `dev` and branches named `dev/*` at the same time.
- Monorepo, not submodules: a single PR may touch multiple areas (`backend` + `common` + `miniapp`) when the change genuinely spans them. Don't split one logical change into separate per-area branches/PRs just to keep areas isolated — that only adds merge/rebase overhead.
- Keep local and remote branch names in sync: don't let the same branch carry different names locally vs. on `origin`, and don't keep a stale remote branch (e.g. an old integration branch name) around once it's been superseded — delete it after confirming the replacement is pushed and tracked correctly.
