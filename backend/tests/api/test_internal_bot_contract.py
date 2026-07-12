from __future__ import annotations

from fastapi import FastAPI
import pytest

from unitkeeper_backend.api.dependencies.internal import require_internal_auth
from unitkeeper_backend.api.router import build_api_router
from unitkeeper_backend.config import settings
from unitkeeper_backend.domain.errors import AuthenticationError


def test_internal_bot_routes_are_registered_under_v1_prefix() -> None:
    app = FastAPI()
    app.include_router(build_api_router())
    paths = set(app.openapi()["paths"])

    assert "/api/v1/internal/bot/users/ensure" in paths
    assert "/api/v1/internal/bot/users/{telegram_user_id}/context" in paths
    assert "/api/v1/internal/bot/task-logs/{log_id}/approve" in paths
    assert "/api/v1/internal/bot/task-logs/{log_id}/reject" in paths
    assert "/api/v1/internal/bot/notifications/outbox" in paths
    assert "/api/v1/internal/bot/notifications/{event_id}/ack" in paths
    assert "/api/v1/internal/bot/notifications/{event_id}/fail" in paths


@pytest.mark.asyncio
async def test_internal_auth_rejects_when_secret_not_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "internal_bot_secret", "")

    with pytest.raises(AuthenticationError):
        await require_internal_auth(x_internal_auth="anything")


@pytest.mark.asyncio
async def test_internal_auth_rejects_on_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "internal_bot_secret", "expected-secret")

    with pytest.raises(AuthenticationError):
        await require_internal_auth(x_internal_auth="wrong-secret")


@pytest.mark.asyncio
async def test_internal_auth_rejects_when_header_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "internal_bot_secret", "expected-secret")

    with pytest.raises(AuthenticationError):
        await require_internal_auth(x_internal_auth=None)


@pytest.mark.asyncio
async def test_internal_auth_passes_on_matching_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "internal_bot_secret", "expected-secret")

    await require_internal_auth(x_internal_auth="expected-secret")
