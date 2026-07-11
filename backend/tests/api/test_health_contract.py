from __future__ import annotations

from fastapi import FastAPI

from unitkeeper_backend.api.router import build_api_router


def test_health_route_is_exposed_under_v1_prefix() -> None:
    app = FastAPI()
    app.include_router(build_api_router())
    paths = set(app.openapi()["paths"])

    assert "/api/v1/health" in paths
