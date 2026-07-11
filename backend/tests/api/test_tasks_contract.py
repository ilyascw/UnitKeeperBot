from __future__ import annotations

from fastapi import FastAPI

from unitkeeper_backend.api.router import build_api_router


def test_task_management_routes_are_registered_under_v1_prefix() -> None:
    app = FastAPI()
    app.include_router(build_api_router())
    paths = set(app.openapi()["paths"])

    assert "/api/v1/tasks" in paths
    assert "/api/v1/tasks/import" in paths
    assert "/api/v1/tasks/{task_id}" in paths
    assert "/api/v1/tasks/{task_id}/increase-frequency" in paths
    assert "/api/v1/tasks/{task_id}/decrease-frequency" in paths
