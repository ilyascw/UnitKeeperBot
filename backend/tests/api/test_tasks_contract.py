from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from fastapi import FastAPI

from unitkeeper_backend.api.router import build_api_router
from unitkeeper_backend.api.schemas.common import TaskResponse
from unitkeeper_backend.application.models import TaskInfo


def test_task_management_routes_are_registered_under_v1_prefix() -> None:
    app = FastAPI()
    app.include_router(build_api_router())
    paths = set(app.openapi()["paths"])

    assert "/api/v1/tasks" in paths
    assert "/api/v1/tasks/import" in paths
    assert "/api/v1/tasks/{task_id}" in paths
    assert "/api/v1/tasks/{task_id}/increase-frequency" in paths
    assert "/api/v1/tasks/{task_id}/decrease-frequency" in paths
    assert "/api/v1/task-logs/pending-approval" in paths
    assert "/api/v1/task-logs/mine" in paths
    assert "/api/v1/task-logs/{log_id}" in paths
    assert "/api/v1/groups/current/task-logs" in paths
    assert "/api/v1/balances/me" in paths
    assert "/api/v1/balances/transfer-candidates" in paths
    assert "/api/v1/balances/transfers" in paths
    assert "/api/v1/balances/transactions" in paths


def test_task_response_exposes_creation_time() -> None:
    created_at = datetime(2026, 8, 10, 12, 30, tzinfo=UTC)
    task = TaskInfo(
        id=1,
        group_id=2,
        title="Wash dishes",
        frequency_per_sprint=3,
        unit_cost=Decimal("5.00"),
        deleted_at=None,
        created_at=created_at,
    )

    response = TaskResponse.model_validate(task)

    assert response.created_at == created_at
