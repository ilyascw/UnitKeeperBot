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

## Working Rules
- New business logic goes to backend services, not to bot handlers or miniapp UI code.
- Bot and miniapp should depend on backend contracts; direct business logic duplication is not allowed.
- Shared DB models and migrations live in `common`.
- Each migrated feature should be traceable back to the legacy artifact in [`docs/legacy-functionality.md`](/Users/ilaskvorcov/Desktop/дело/unitkeeper/docs/legacy-functionality.md).
- Use ruff, mypy, uv, tests
