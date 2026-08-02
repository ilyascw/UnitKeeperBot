# UnitKeeper Bot

Thin Telegram bot for notifications and routes into the UnitKeeper Mini App. It does not access the database or implement group, task, sprint, or balance rules.

## Configuration

Copy `.env.example` to `.env` and configure:

- `UNITKEEPER_BOT_TOKEN`: Telegram bot token.
- `UNITKEEPER_BACKEND_BASE_URL`: backend API base URL, including `/api/v1`.
- `UNITKEEPER_INTERNAL_BOT_SECRET`: shared secret sent as `X-Internal-Auth` to `/internal/bot/*`.
- `UNITKEEPER_MINIAPP_URL`: HTTPS URL opened by Telegram's Web App button.
- `UNITKEEPER_TGPROXY`: optional HTTP or SOCKS proxy URL used for Telegram API requests.

The backend must configure the same secret as `INTERNAL_BOT_SECRET`.

## Commands

- `/start` ensures the Telegram user through the backend and opens the Mini App.
- `/help` and `/about` route users to the Mini App.
- Legacy commands and free text receive a Mini App redirect.

## Development

```bash
uv sync --extra dev
uv run ruff check src tests
uv run pytest
uv run python -m unitkeeper_bot.main
```
