from __future__ import annotations

from unitkeeper_backend.api.router import build_api_router


def test_health_route_is_exposed_under_v1_prefix() -> None:
    router = build_api_router()
    paths = {route.path for route in router.routes}

    assert "/api/v1/health" in paths
