from __future__ import annotations

from datetime import date, datetime, timezone


class UtcClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)

    def today(self) -> date:
        return self.now().date()
