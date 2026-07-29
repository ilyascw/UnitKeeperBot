FROM ghcr.io/astral-sh/uv:0.10.6 AS uv

FROM python:3.11-slim

ENV PATH="/app/backend/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY --from=uv /uv /uvx /bin/

COPY common/pyproject.toml common/uv.lock common/README.md ./common/
COPY common/src/ ./common/src/

COPY backend/pyproject.toml backend/uv.lock backend/README.md ./backend/
COPY backend/src/ ./backend/src/

RUN uv sync --project backend --frozen --no-dev --no-editable

USER 65532:65532
WORKDIR /app/backend

EXPOSE 8000
CMD ["uvicorn", "unitkeeper_backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
