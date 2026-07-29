.PHONY: install lint format-check typecheck test frontend check

install:
	cd common && uv sync --frozen --group dev
	cd backend && uv sync --frozen --extra dev --group dev
	cd bot && uv sync --frozen --extra dev
	cd miniapp && npm ci

lint:
	cd common && uv run ruff check .
	cd backend && uv run ruff check .
	cd bot && uv run ruff check .
	cd miniapp && npm run lint

format-check:
	cd common && uv run ruff format --check .
	cd backend && uv run ruff format --check .
	cd bot && uv run ruff format --check .

typecheck:
	cd common && uv run mypy
	cd backend && uv run mypy
	cd bot && uv run mypy
	cd miniapp && npm run typecheck

test:
	cd common && uv run pytest -m "not integration"
	cd backend && uv run pytest
	cd bot && uv run pytest

frontend:
	cd miniapp && npm run build

check: lint format-check typecheck test frontend
