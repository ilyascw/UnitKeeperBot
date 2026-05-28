from __future__ import annotations

from unitkeeper_backend.api.router import build_api_router


def test_task_management_routes_are_registered_under_v1_prefix() -> None:
    router = build_api_router()
    paths = {route.path for route in router.routes}

    assert "/api/v1/tasks" in paths
    assert "/api/v1/tasks/import" in paths
    assert "/api/v1/tasks/{task_id}" in paths
    assert "/api/v1/tasks/{task_id}/increase-frequency" in paths
    assert "/api/v1/tasks/{task_id}/decrease-frequency" in paths
