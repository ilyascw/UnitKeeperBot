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

## Working Rules
- New business logic goes to backend services, not to bot handlers or miniapp UI code.
- Bot and miniapp should depend on backend contracts; direct business logic duplication is not allowed.
- Shared DB models and migrations live in `common`.
- Each migrated feature should be traceable back to the legacy artifact in [`docs/legacy-functionality.md`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/docs/legacy-functionality.md).
- Use ruff, mypy, uv, tests
- Python services must use `pyproject.toml` as the project entrypoint for dependencies and tooling; do not add ad hoc dependency files when `pyproject.toml` is appropriate.
- Use `uv` to create and manage the virtual environment for the service you are working on.
- The virtual environment must live inside the working service directory, not at repo root. Example: when working on [`backend`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/backend), create and activate [`backend/.venv`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/backend/.venv).
