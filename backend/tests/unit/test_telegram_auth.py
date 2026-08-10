from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from urllib.parse import urlencode

from unitkeeper_backend.infrastructure.auth.telegram import TelegramWebAppVerifier


def _signed_init_data(*, bot_token: str, user: dict[str, object]) -> str:
    pairs = {
        "auth_date": str(int(datetime.now(timezone.utc).timestamp())),
        "query_id": "test-query-id",
        "user": json.dumps(user, separators=(",", ":")),
    }
    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(pairs.items()))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    pairs["hash"] = hmac.new(secret, data_check_string.encode(), hashlib.sha256).hexdigest()
    return urlencode(pairs)


def test_verifier_extracts_authoritative_photo_url() -> None:
    bot_token = "123456:test-token"
    init_data = _signed_init_data(
        bot_token=bot_token,
        user={
            "id": 42,
            "first_name": "Ivan",
            "photo_url": "https://t.me/i/userpic/320/avatar.svg",
        },
    )

    identity = TelegramWebAppVerifier(
        bot_token=bot_token,
        max_age_seconds=60,
    ).verify(init_data)

    assert identity.photo_url == "https://t.me/i/userpic/320/avatar.svg"
    assert identity.photo_url_is_authoritative is True


def test_verifier_marks_missing_photo_as_authoritative_none() -> None:
    bot_token = "123456:test-token"
    init_data = _signed_init_data(
        bot_token=bot_token,
        user={"id": 42, "first_name": "Ivan"},
    )

    identity = TelegramWebAppVerifier(
        bot_token=bot_token,
        max_age_seconds=60,
    ).verify(init_data)

    assert identity.photo_url is None
    assert identity.photo_url_is_authoritative is True
