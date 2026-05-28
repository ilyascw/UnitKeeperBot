from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP

from db.enums import Weekday
from unitkeeper_backend.domain.errors import ValidationError

HUNDRED = Decimal("100.00")
ZERO = Decimal("0.00")
TWO_PLACES = Decimal("0.01")


@dataclass(frozen=True, slots=True)
class SprintWindow:
    period_start: date
    period_end: date

    @property
    def starts_at(self) -> datetime:
        return datetime.combine(self.period_start, time.min, tzinfo=timezone.utc)

    @property
    def ends_before(self) -> datetime:
        return datetime.combine(self.period_end + timedelta(days=1), time.min, tzinfo=timezone.utc)


def quantize(value: Decimal) -> Decimal:
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def weekday_index(weekday: Weekday) -> int:
    mapping = {
        Weekday.MONDAY: 0,
        Weekday.TUESDAY: 1,
        Weekday.WEDNESDAY: 2,
        Weekday.THURSDAY: 3,
        Weekday.FRIDAY: 4,
        Weekday.SATURDAY: 5,
        Weekday.SUNDAY: 6,
    }
    return mapping[weekday]


def current_sprint_window(*, today: date, start_weekday: Weekday, duration_days: int) -> SprintWindow:
    if duration_days <= 0 or duration_days % 7 != 0:
        raise ValueError("Sprint duration must be positive and divisible by 7")

    days_back = (today.weekday() - weekday_index(start_weekday)) % 7
    period_start = today - timedelta(days=days_back)
    period_end = period_start + timedelta(days=duration_days - 1)
    return SprintWindow(period_start=period_start, period_end=period_end)


def validate_member_weights(
    *,
    active_user_ids: list[int],
    weights_by_user_id: dict[int, Decimal],
) -> dict[int, Decimal]:
    """Validate manual weight assignment.

    Ensures the mapping covers exactly the active members, contains no negative
    values, and sums to 100. Returns the quantized mapping ready to persist.
    """
    expected = set(active_user_ids)
    provided = set(weights_by_user_id)
    if provided != expected:
        missing = sorted(expected - provided)
        extra = sorted(provided - expected)
        details = []
        if missing:
            details.append(f"missing weights for users {missing}")
        if extra:
            details.append(f"unexpected weights for users {extra}")
        raise ValidationError("Weights must cover every active member: " + "; ".join(details))

    quantized: dict[int, Decimal] = {}
    for user_id, value in weights_by_user_id.items():
        if value < ZERO:
            raise ValidationError(f"Weight for user {user_id} must not be negative")
        quantized[user_id] = quantize(value)

    total = sum(quantized.values(), start=ZERO)
    if total != HUNDRED:
        raise ValidationError(f"Weights must sum to 100, got {total}")
    return quantized


def distribute_equally(member_user_ids: list[int]) -> dict[int, Decimal]:
    if not member_user_ids:
        return {}

    ordered_ids = sorted(member_user_ids)
    count = Decimal(len(ordered_ids))
    base = quantize(HUNDRED / count)
    weights = {user_id: base for user_id in ordered_ids}
    remainder = HUNDRED - sum(weights.values(), start=ZERO)

    if remainder != ZERO:
        weights[ordered_ids[-1]] = quantize(weights[ordered_ids[-1]] + remainder)

    return weights


def planned_units(*, total_task_units: Decimal, weight_percent: Decimal) -> Decimal:
    return quantize(total_task_units * weight_percent / HUNDRED)


def progress_percent(*, completed_units: Decimal, planned_units_total: Decimal) -> Decimal:
    if planned_units_total <= ZERO:
        return ZERO
    return quantize(completed_units * HUNDRED / planned_units_total)
