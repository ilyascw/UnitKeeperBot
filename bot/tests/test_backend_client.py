from __future__ import annotations

import httpx
import pytest

from unitkeeper_bot.backend.client import BackendClient, BackendTransportError, TelegramUser


@pytest.mark.asyncio
async def test_client_uses_internal_auth_and_maps_context() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path.endswith("/ensure"):
            return httpx.Response(200, json={"id": 12})
        return httpx.Response(200, json={"user": {"id": 12}, "membership": None, "group": None})

    client = BackendClient(
        base_url="https://backend.example/api/v1",
        internal_secret="internal-secret",
        timeout_seconds=1,
        transport=httpx.MockTransport(handler),
    )
    try:
        await client.ensure_user(TelegramUser(12, "alice", "Alice", None, "en", False))
        context = await client.get_current_context(telegram_user_id=12)
    finally:
        await client.close()

    assert context.has_active_group is False
    assert [request.headers["X-Internal-Auth"] for request in requests] == ["internal-secret"] * 2
    assert requests[0].url.path == "/api/v1/internal/bot/users/ensure"
    assert requests[1].url.path == "/api/v1/internal/bot/users/12/context"


@pytest.mark.asyncio
async def test_client_wraps_backend_http_errors() -> None:
    client = BackendClient(
        base_url="https://backend.example/api/v1",
        internal_secret="internal-secret",
        timeout_seconds=1,
        transport=httpx.MockTransport(lambda request: httpx.Response(401, request=request)),
    )
    try:
        with pytest.raises(BackendTransportError):
            await client.get_current_context(telegram_user_id=12)
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_client_lists_and_acknowledges_outbox_events() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path.endswith("/outbox"):
            return httpx.Response(
                200,
                json={
                    "items": [
                        {
                            "id": "00000000-0000-0000-0000-000000000001",
                            "event_type": "sprint_personal_report",
                            "recipient_user_id": 12,
                            "payload": {"completed_units": "4"},
                            "deep_link_path": "/progress",
                            "correlation_id": "worker-1",
                        }
                    ]
                },
            )
        return httpx.Response(200, json={})

    client = BackendClient(
        base_url="https://backend.example/api/v1",
        internal_secret="internal-secret",
        timeout_seconds=1,
        transport=httpx.MockTransport(handler),
    )
    try:
        events = await client.list_notification_outbox()
        await client.acknowledge_notification(event_id=events[0].id)
    finally:
        await client.close()

    assert events[0].recipient_user_id == 12
    assert requests[0].url.path.endswith("/notifications/outbox")
    assert requests[1].url.path.endswith("/notifications/00000000-0000-0000-0000-000000000001/ack")
