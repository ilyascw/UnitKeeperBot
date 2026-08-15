from __future__ import annotations

from datetime import datetime, timezone


class UtcClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)
