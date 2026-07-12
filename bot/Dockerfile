FROM python:3.11-slim

WORKDIR /app

COPY bot/pyproject.toml bot/PLAN.md ./bot/
COPY bot/src/ ./bot/src/

RUN pip install -e ./bot

WORKDIR /app/bot

CMD ["python", "-m", "unitkeeper_bot.main"]
