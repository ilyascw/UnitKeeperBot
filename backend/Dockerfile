FROM python:3.11-slim

WORKDIR /app

COPY common/pyproject.toml common/README.md ./common/
COPY common/src/ ./common/src/

COPY backend/pyproject.toml backend/PLAN.md ./backend/
COPY backend/src/ ./backend/src/

RUN pip install -e ./common -e ./backend

WORKDIR /app/backend

CMD ["uvicorn", "unitkeeper_backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
