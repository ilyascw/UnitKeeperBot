# UnitKeeper Backend

FastAPI-сервис с бизнес-правилами групп, задач, approvals, спринтов и балансов.

```bash
cp .env.example .env
uv sync --frozen --extra dev --group dev
uv run uvicorn unitkeeper_backend.main:app --reload
```

Проверки:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest
```

OpenAPI доступен по адресу `http://localhost:8000/docs`.
