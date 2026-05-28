from __future__ import annotations

from datetime import date
from decimal import Decimal

from db.enums import Weekday
from unitkeeper_backend.domain.services.sprint_math import current_sprint_window, distribute_equally


def test_current_sprint_window_uses_previous_matching_weekday() -> None:
    window = current_sprint_window(
        today=date(2026, 3, 18),
        start_weekday=Weekday.MONDAY,
        duration_days=14,
    )

    assert window.period_start == date(2026, 3, 16)
    assert window.period_end == date(2026, 3, 29)


def test_distribute_equally_keeps_total_at_exactly_hundred() -> None:
    weights = distribute_equally([20, 10, 30])

    assert weights == {
        10: Decimal("33.33"),
        20: Decimal("33.33"),
        30: Decimal("33.34"),
    }
    assert sum(weights.values()) == Decimal("100.00")
