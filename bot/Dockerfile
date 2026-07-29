FROM ghcr.io/astral-sh/uv:0.10.6 AS uv

FROM python:3.11-slim

ENV PATH="/app/bot/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY --from=uv /uv /uvx /bin/
COPY bot/pyproject.toml bot/uv.lock bot/README.md ./bot/
COPY bot/src/ ./bot/src/

RUN uv sync --project bot --frozen --no-dev --no-editable

USER 65532:65532
WORKDIR /app/bot

CMD ["python", "-m", "unitkeeper_bot.main"]
