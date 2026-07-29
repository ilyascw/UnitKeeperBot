from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from urllib.parse import parse_qsl

from unitkeeper_backend.application.models import TelegramIdentity
from unitkeeper_backend.domain.errors import AuthenticationError


class TelegramWebAppVerifier:
    def __init__(self, *, bot_token: str, max_age_seconds: int) -> None:
        self._bot_token = bot_token
        self._max_age_seconds = max_age_seconds

    def verify(self, init_data: str) -> TelegramIdentity:
        pairs = dict(parse_qsl(init_data, keep_blank_values=True))
        provided_hash = pairs.pop("hash", None)
        if not provided_hash:
            raise AuthenticationError("Telegram init data hash is missing")

        data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(pairs.items()))
        secret = hmac.new(b"WebAppData", self._bot_token.encode("utf-8"), hashlib.sha256).digest()
        expected_hash = hmac.new(
            secret,
            data_check_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(provided_hash, expected_hash):
            raise AuthenticationError("Telegram init data signature is invalid")

        auth_date_raw = pairs.get("auth_date")
        if auth_date_raw is None:
            raise AuthenticationError("Telegram init data auth_date is missing")
        auth_date = datetime.fromtimestamp(int(auth_date_raw), tz=timezone.utc)
        age = (datetime.now(timezone.utc) - auth_date).total_seconds()
        if age > self._max_age_seconds:
            raise AuthenticationError("Telegram init data is too old")

        user_payload = pairs.get("user")
        if user_payload is None:
            raise AuthenticationError("Telegram init data user payload is missing")
        user = json.loads(user_payload)
        return TelegramIdentity(
            user_id=int(user["id"]),
            username=user.get("username"),
            first_name=user.get("first_name"),
            last_name=user.get("last_name"),
            language_code=user.get("language_code"),
            is_bot=bool(user.get("is_bot", False)),
        )
