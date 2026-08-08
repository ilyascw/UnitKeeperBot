# Repo instructions

## Project

UnitKeeper is a Telegram Mini App for recurring household/team task tracking,
load-weighted sprints, peer-approval, and unit-based settlement between group
members. Monorepo: `backend` (FastAPI), `bot` (aiogram, thin transport),
`miniapp` (React/TS), `common` (SQLAlchemy models + Alembic). GitHub repo:
`ilyascw/UnitKeeperBot`.

Read before working, so context doesn't have to be rebuilt from scratch each
session (still read whatever's specific to the task at hand, but these cover
the recurring ground):

- [README.md](README.md) — stack, architecture diagram, run instructions,
  quality gates, current limitations.
- [architecture.md](architecture.md) — system design in depth.
- [docs/product.md](docs/product.md) — domain model: sprints, units, weights,
  peer-approval lifecycle, settlement.
- [docs/bot/recovery-operations.md](docs/bot/recovery-operations.md) — bot
  outbox/notification recovery runbook.
- [docs/common/legacy-data-bootstrap.md](docs/common/legacy-data-bootstrap.md) —
  legacy CSV import (see also `backend/scripts/import_legacy_csv.py`).
- [scripts/dev/README.md](scripts/dev/README.md) — local 2-user browser dev
  setup (docker-compose backend+DB + two Vite dev servers pre-authenticated
  as different Telegram users), for manually testing without real Telegram.
- `UnitKeeperBot/` is a **separate, older, nested git repo** (the legacy bot
  this project migrated from) — `cd`-ing into it silently switches git
  context; watch for that when running git commands.

## Git commits

Do not add `Co-Authored-By: Claude ...` or `Claude-Session: ...` trailers to
commit messages in this repo. Write commit messages as if authored solely by
the human developer.

## CI

Commits that touch only documentation/instructions (this file, README.md,
architecture.md, docs/**) and no code, config, schema, or dependency files
should end with `[skip ci]` in the subject line — no need to burn a full
CI matrix run for a doc-only change.

## Git flow

`dev` is the integration branch — feature/fix branches merge into `dev` via
PR; `dev` is periodically promoted to `main` via PR once manually tested.

## Releases

Tag `main` after each `dev` → `main` promotion and publish a GitHub Release
(`gh release create`) with user-facing notes (what changed, not commit logs).
Version scheme: semver, starting at `v0.1.0`. The first release must state
explicitly that it marks the start of formal release tracking — don't let it
read like a first version shipped from nothing, since the project already had
months of real usage before this.
