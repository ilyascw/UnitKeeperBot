# Local 2-user dev environment

Spin up the backend + DB in Docker and two miniapp dev servers, each
pre-authenticated as a different Telegram user, without needing the real
Telegram app.

## One-time / whenever init data expires (24h TTL)

```bash
# Regenerate signed initData for the two dev users (Alex id=900000001,
# Mia id=900000002), from the TELEGRAM_BOT_TOKEN in the repo-root .env.
python3 scripts/dev/gen_init_data.py

# Copy the two printed VITE_DEV_INIT_DATA lines into
# miniapp/.env.user1 and miniapp/.env.user2 (VITE_DEV_INIT_DATA=...).
```

## Every time

```bash
# 1. Backend + Postgres
docker compose up -d db migrate backend

# 2. Two miniapp dev servers, one per user
cd miniapp
npx vite --mode user1 --port 5173 &   # Alex  -> http://localhost:5173
npx vite --mode user2 --port 5174 &   # Mia   -> http://localhost:5174
```

Open both URLs in separate browser windows (or a normal + incognito window —
they're different origins/ports so sessions don't collide). Use one as the
group owner (create a group) and join with the other via the group's join
code, then exercise both sides of approve/reject/cancel flows.

## Notes

- `miniapp/.env.user1` / `.env.user2` are gitignored (`.env.*` pattern) —
  they hold signed dev-only Telegram init data, not secrets by themselves,
  but scoped to local use only.
- `TELEGRAM_AUTH_MAX_AGE_SECONDS=86400` in the root `.env`, so generated
  init data is valid for 24h from generation; rerun `gen_init_data.py` after
  that.
- The root `.env` also carries `TELEGRAM_BOT_TOKEN` (from `backend/.env`,
  a real-but-unused-in-prod dev bot) so the backend's signature check
  matches what `gen_init_data.py` signs with.
- Stop everything with `docker compose down` (add `-v` to also drop the
  Postgres volume) and `kill` the two `vite` processes.
