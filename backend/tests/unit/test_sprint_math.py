from __future__ import annotations

from datetime import date, datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest
from db.enums import Weekday

from unitkeeper_backend.domain.services.sprint_math import (
    SprintWindow,
    current_sprint_window,
    distribute_equally,
)

UTC = ZoneInfo("UTC")
MOSCOW = ZoneInfo("Europe/Moscow")
BERLIN = ZoneInfo("Europe/Berlin")  # observes DST, unlike Moscow


def noon_utc(day: date) -> datetime:
    """An instant safely inside ``day`` for any zone within a few hours of UTC."""
    return datetime.combine(day, time(12), tzinfo=UTC)


def test_current_sprint_window_uses_previous_matching_weekday() -> None:
    window = current_sprint_window(
        now=noon_utc(date(2026, 3, 18)),
        zone=UTC,
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
        now=noon_utc(date(2026, 3, 16)),  # Monday, first day of the window
        zone=UTC,
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
        now=noon_utc(date(2026, 3, 16) + timedelta(days=duration_days - 1)),  # last day
        zone=UTC,
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
        now=noon_utc(expected_start + timedelta(days=duration_days - 1)),  # last day of cycle
        zone=UTC,
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
        now=noon_utc(anchor),
        zone=UTC,
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
            now=noon_utc(date(2026, 3, 18)),
            zone=UTC,
            start_weekday=Weekday.MONDAY,
            duration_days=duration_days,
            anchor=date(2026, 3, 16),
        )


def test_window_bounds_follow_the_group_zone_not_utc() -> None:
    window = current_sprint_window(
        now=datetime(2026, 8, 16, 12, tzinfo=UTC),
        zone=MOSCOW,
        start_weekday=Weekday.MONDAY,
        duration_days=7,
        anchor=date(2026, 8, 10),
    )

    assert window.period_start == date(2026, 8, 10)
    assert window.period_end == date(2026, 8, 16)
    assert window.starts_at == datetime(2026, 8, 10, tzinfo=MOSCOW)
    assert window.ends_before == datetime(2026, 8, 17, tzinfo=MOSCOW)
    # 2026-08-17T00:00+03:00 is 2026-08-16T21:00Z, not 2026-08-17T00:00Z.
    assert window.ends_before == datetime(2026, 8, 16, 21, tzinfo=UTC)
    # A completion late on the final local day still falls inside the window.
    assert window.starts_at <= datetime(2026, 8, 16, 23, 30, tzinfo=MOSCOW) < window.ends_before


def test_local_midnight_boundary_belongs_to_the_next_window() -> None:
    boundary = datetime(2026, 8, 17, tzinfo=MOSCOW)
    ending = SprintWindow(period_start=date(2026, 8, 10), period_end=date(2026, 8, 16), zone=MOSCOW)

    assert not ending.has_ended_at(boundary - timedelta(seconds=1))
    assert ending.has_ended_at(boundary)

    following = current_sprint_window(
        now=boundary,
        zone=MOSCOW,
        start_weekday=Weekday.MONDAY,
        duration_days=7,
        anchor=date(2026, 8, 10),
    )
    assert following.period_start == date(2026, 8, 17)
    assert following.starts_at == boundary


def test_window_bounds_absorb_a_dst_transition_in_both_directions() -> None:
    # Europe/Berlin springs forward 2026-03-29 (23-hour day) and falls back
    # 2026-10-25 (25-hour day). Both windows must still run local-midnight to
    # local-midnight, so the real time they span differs by an hour from a plain
    # 7 days. Spans are measured in UTC: subtracting two datetimes that share a
    # tzinfo is wall-clock arithmetic and would hide the transition entirely.
    def real_span(window: SprintWindow) -> timedelta:
        return window.ends_before.astimezone(UTC) - window.starts_at.astimezone(UTC)

    spring = SprintWindow(period_start=date(2026, 3, 23), period_end=date(2026, 3, 29), zone=BERLIN)
    assert spring.starts_at == datetime(2026, 3, 23, tzinfo=BERLIN)
    assert spring.ends_before == datetime(2026, 3, 30, tzinfo=BERLIN)
    assert real_span(spring) == timedelta(days=7) - timedelta(hours=1)

    autumn = SprintWindow(
        period_start=date(2026, 10, 19), period_end=date(2026, 10, 25), zone=BERLIN
    )
    assert real_span(autumn) == timedelta(days=7) + timedelta(hours=1)


def test_distribute_equally_keeps_total_at_exactly_hundred() -> None:
    weights = distribute_equally([20, 10, 30])

    assert weights == {
        10: Decimal("33.33"),
        20: Decimal("33.33"),
        30: Decimal("33.34"),
    }
    assert sum(weights.values()) == Decimal("100.00")
