.PHONY: up down migrate revision install lint typecheck test test-migrations check

COMPOSE ?= docker compose -f docker-compose.dev.yml
TEST_COMPOSE ?= docker compose -p unitkeeper-common-test -f docker-compose.test.yml

up:
	$(COMPOSE) up -d db

down:
	$(COMPOSE) down

migrate:
	PYTHONPATH=src alembic upgrade head

revision:
	@if [ -z "$(m)" ]; then echo "Error: message is required. Use make revision m=\"message\""; exit 1; fi
	PYTHONPATH=src alembic revision --autogenerate -m "$(m)"

install:
	uv sync --group dev

lint:
	uv run ruff check src tests

typecheck:
	uv run mypy

test:
	uv run pytest -m "not integration"

test-migrations:
	@set -eu; \
	cleanup() { $(TEST_COMPOSE) down --volumes --remove-orphans; }; \
	trap cleanup EXIT; \
	cleanup; \
	$(TEST_COMPOSE) up --wait --quiet-pull; \
	TEST_DATABASE_URL=postgresql+asyncpg://unitkeeper:unitkeeper@127.0.0.1:5433/unitkeeper_common_test uv run pytest -m integration

check: lint typecheck test
