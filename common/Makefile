.PHONY: up down migrate revision

COMPOSE ?= docker compose -f docker-compose.dev.yml

up:
	$(COMPOSE) up -d db

down:
	$(COMPOSE) down

migrate:
	PYTHONPATH=src alembic upgrade head

revision:
	@if [ -z "$(m)" ]; then echo "Error: message is required. Use make revision m=\"message\""; exit 1; fi
	PYTHONPATH=src alembic revision --autogenerate -m "$(m)"
