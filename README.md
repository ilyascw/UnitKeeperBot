# UnitKeeper

This branch is the migration workspace for the next UnitKeeper architecture.

The old Telegram bot is still the legacy source of truth for product behavior, but the new system is being split into explicit layers:

- `miniapp` - Telegram Mini App, the main user interface.
- `backend` - FastAPI service with business rules, auth, APIs, schedulers, and integrations.
- `common` - shared SQLAlchemy models, Alembic migrations, and database wiring.
- `bot` - thin Telegram bot for notifications, deep links, and minimal fallback actions.
- `docs` - migration notes, delivery backlog, and legacy behavior mapping.
- `UnitKeeperBot` - legacy bot repository kept here for reference during migration.

Core rule: new business logic belongs in `backend`, not in bot handlers or miniapp UI code.

The active migration map is in `docs/layer-delivery-map.md`; legacy behavior is tracked in `docs/legacy-functionality.md`.
