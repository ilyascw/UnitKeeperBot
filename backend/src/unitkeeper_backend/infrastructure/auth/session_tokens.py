from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone

from unitkeeper_backend.domain.errors import AuthenticationError


class HmacSessionTokenManager:
    def __init__(self, *, secret: str, ttl_seconds: int) -> None:
        self._secret = secret.encode("utf-8")
        self._ttl_seconds = ttl_seconds

    def issue(self, *, user_id: int, issued_at: datetime) -> tuple[str, datetime]:
        expires_at = issued_at + timedelta(seconds=self._ttl_seconds)
        payload = {
            "user_id": user_id,
            "exp": int(expires_at.timestamp()),
        }
        payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        signature = (
            hmac.new(self._secret, payload_bytes, hashlib.sha256).hexdigest().encode("ascii")
        )
        token = base64.urlsafe_b64encode(payload_bytes + b"." + signature).decode("ascii")
        return token, expires_at

    def verify(self, token: str) -> int:
        try:
            decoded = base64.urlsafe_b64decode(token.encode("ascii"))
            payload_bytes, signature = decoded.rsplit(b".", 1)
        except Exception as exc:
            raise AuthenticationError("Malformed session token") from exc

        expected_signature = (
            hmac.new(self._secret, payload_bytes, hashlib.sha256).hexdigest().encode("ascii")
        )
        if not hmac.compare_digest(signature, expected_signature):
            raise AuthenticationError("Invalid session token signature")

        payload = json.loads(payload_bytes.decode("utf-8"))
        expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        if expires_at <= datetime.now(timezone.utc):
            raise AuthenticationError("Session token has expired")
        return int(payload["user_id"])
