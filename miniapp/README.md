# UnitKeeper Mini App

The main user interface for UnitKeeper, delivered as a Telegram Mini App.

## Stack

- **Vite** — build tool and dev server
- **React + TypeScript** — UI
- **Telegram UI Kit** (`@telegram-apps/telegram-ui`) — native Telegram look and feel
- **Telegram Mini Apps SDK** (`@telegram-apps/sdk-react`) — runtime, theme, init data
- **TanStack Query** — data fetching, caching, loading/error states
- **React Router** — client-side routing

## Project layout

```
src/
  api/         # typed backend client, contract types, endpoints, query hooks
  auth/        # session bootstrap from Telegram init data + token storage
  components/  # app shell: layout, loader, error state, error boundary
  config/      # validated build-time configuration (env.ts)
  routes/      # route table and path registry
  screens/     # one component per screen
  telegram/    # SDK init, launch-data resolution, appearance hook
  App.tsx      # providers + shell composition
  main.tsx     # entrypoint (SDK init + render)
```

The app never sends a user id to the backend. Authentication exchanges the
signed Telegram **init data** for a session token (`POST /auth/telegram`); the
backend derives the user from the signature. The token is persisted and
restored on reload (validated against `GET /auth/me`).

## Backend contract used in this foundation

- `POST /auth/telegram` `{ init_data }` → session `{ access_token, expires_at, context }`
- `GET /auth/me` → current context (user / membership / group)
- `GET /groups/current` → current group card (404 ⇒ onboarding)

Contract types live in `src/api/types.ts` and mirror
`backend/src/unitkeeper_backend/api/schemas`.

## Developer setup

Requires Node.js 20+ and npm.

```bash
cd miniapp
npm install
cp .env.example .env        # then edit values
npm run dev                 # http://localhost:5173
```

### Environment variables

| Variable               | Purpose                                                                 |
| ---------------------- | ----------------------------------------------------------------------- |
| `VITE_API_BASE_URL`    | Backend base URL incl. `/api/v1` (default `http://localhost:8000/api/v1`) |
| `VITE_TELEGRAM_DEBUG`  | `true` to enable verbose Telegram SDK logging                           |
| `VITE_DEV_INIT_DATA`   | Dev-only raw init data to bootstrap auth outside Telegram (never in prod) |

### Running outside Telegram

In a plain browser tab there is no `window.Telegram.WebApp`, so init data
cannot be retrieved and the app shows an "Open from Telegram" state. To develop
screens without Telegram, paste a valid raw init data string into
`VITE_DEV_INIT_DATA`. This is ignored in production builds.

### Running inside Telegram

Expose the dev server over HTTPS (e.g. with a tunnel) and set the Mini App URL
in BotFather to that address. Opening the app from the bot injects real init
data and the full theme.

## Scripts

| Script              | Description                          |
| ------------------- | ------------------------------------ |
| `npm run dev`       | Start the Vite dev server            |
| `npm run build`     | Type-check and build for production  |
| `npm run preview`   | Preview the production build         |
| `npm run typecheck` | Type-check without emitting          |
| `npm run lint`      | Run ESLint                           |
| `npm run format`    | Format with Prettier                 |
```
