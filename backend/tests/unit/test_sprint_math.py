from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest
from db.enums import Weekday

from unitkeeper_backend.domain.services.sprint_math import current_sprint_window, distribute_equally


def test_current_sprint_window_uses_previous_matching_weekday() -> None:
    window = current_sprint_window(
        today=date(2026, 3, 18),
        start_weekday=Weekday.MONDAY,
        duration_days=14,
        anchor=date(2026, 3, 16),
    )

    assert window.period_start == date(2026, 3, 16)
    assert window.period_end == date(2026, 3, 29)


@pytest.mark.parametrize("duration_days", [7, 14, 21, 28])
def test_current_sprint_window_spans_exactly_duration_days_for_any_multiple_of_seven(
    duration_days: int,
) -> None:
    window = current_sprint_window(
        today=date(2026, 3, 16),  # Monday, first day of the window
        start_weekday=Weekday.MONDAY,
        duration_days=duration_days,
        anchor=date(2026, 3, 16),
    )

    assert window.period_start == date(2026, 3, 16)
    assert window.period_end == date(2026, 3, 16) + timedelta(days=duration_days - 1)
    assert (window.period_end - window.period_start).days + 1 == duration_days


@pytest.mark.parametrize("duration_days", [7, 14, 21, 28])
def test_current_sprint_window_is_due_on_its_last_day_for_any_multiple_of_seven(
    duration_days: int,
) -> None:
    window = current_sprint_window(
        today=date(2026, 3, 16) + timedelta(days=duration_days - 1),  # last day of the window
        start_weekday=Weekday.MONDAY,
        duration_days=duration_days,
        anchor=date(2026, 3, 16),
    )

    assert window.period_start == date(2026, 3, 16)
    assert window.period_end == date(2026, 3, 16) + timedelta(days=duration_days - 1)


@pytest.mark.parametrize("cycles_elapsed", [0, 1, 2, 5])
def test_current_sprint_window_stays_aligned_across_many_multi_week_cycles(
    cycles_elapsed: int,
) -> None:
    duration_days = 21
    anchor = date(2026, 1, 5)  # Monday
    expected_start = anchor + timedelta(days=cycles_elapsed * duration_days)

    window = current_sprint_window(
        today=expected_start + timedelta(days=duration_days - 1),  # last day of that cycle
        start_weekday=Weekday.MONDAY,
        duration_days=duration_days,
        anchor=anchor,
    )

    assert window.period_start == expected_start
    assert window.period_end == expected_start + timedelta(days=duration_days - 1)


def test_current_sprint_window_aligns_anchor_to_the_start_weekday_before_it() -> None:
    # Group created mid-week (Thursday); the first cycle should still start on
    # the preceding Monday, exactly like the weekday-only legacy behavior did.
    anchor = date(2026, 3, 12)  # Thursday
    window = current_sprint_window(
        today=anchor,
        start_weekday=Weekday.MONDAY,
        duration_days=7,
        anchor=anchor,
    )

    assert window.period_start == date(2026, 3, 9)
    assert window.period_end == date(2026, 3, 15)


@pytest.mark.parametrize("duration_days", [0, -7, 10, 1, 8])
def test_current_sprint_window_rejects_duration_not_a_positive_multiple_of_seven(
    duration_days: int,
) -> None:
    with pytest.raises(ValueError):
        current_sprint_window(
            today=date(2026, 3, 18),
            start_weekday=Weekday.MONDAY,
            duration_days=duration_days,
            anchor=date(2026, 3, 16),
        )


def test_distribute_equally_keeps_total_at_exactly_hundred() -> None:
    weights = distribute_equally([20, 10, 30])

    assert weights == {
        10: Decimal("33.33"),
        20: Decimal("33.33"),
        30: Decimal("33.34"),
    }
    assert sum(weights.values()) == Decimal("100.00")
