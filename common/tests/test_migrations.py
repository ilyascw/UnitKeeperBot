from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect

EXPECTED_TABLES = {
    "alembic_version",
    "balance_transactions",
    "balances",
    "group_member_weights",
    "group_memberships",
    "groups",
    "idempotency_keys",
    "notification_delivery_attempts",
    "notification_outbox_events",
    "sprint_member_results",
    "sprint_runs",
    "task_logs",
    "tasks",
    "users",
}


def _sync_database_url(async_database_url: str) -> str:
    return async_database_url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)


@pytest.mark.integration
def test_upgrade_head_applies_to_a_fresh_database() -> None:
    database_url = os.environ.get("TEST_DATABASE_URL")
    if database_url is None:
        pytest.skip("TEST_DATABASE_URL is required for the migration smoke test")

    project_root = Path(__file__).resolve().parents[1]
    environment = {**os.environ, "DATABASE_URL": database_url}
    subprocess.run(
        [sys.executable, "-m", "alembic", "-c", str(project_root / "alembic.ini"), "upgrade", "head"],
        check=True,
        cwd=project_root,
        env=environment,
    )

    sync_engine = create_engine(_sync_database_url(database_url))
    try:
        inspector = inspect(sync_engine)
        assert EXPECTED_TABLES <= set(inspector.get_table_names())
        assert inspector.get_columns("task_logs")
    finally:
        sync_engine.dispose()
