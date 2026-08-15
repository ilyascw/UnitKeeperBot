"""Resolution of a group's stored IANA timezone into a usable ``ZoneInfo``.

Input is validated at the API edge (``api/schemas/groups.py``), so an
unresolvable value here means a corrupt or legacy row. Such a row must not
wedge the sprint-close pass for every *other* group, so resolution degrades to
UTC with a warning that names the group instead of raising.
"""

from __future__ import annotations

import logging
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

logger = logging.getLogger(__name__)

UTC = ZoneInfo("UTC")


def resolve_timezone_name(timezone_name: str | None) -> ZoneInfo | None:
    """Return the zone for ``timezone_name``, or ``None`` if it is unusable."""
    if not timezone_name:
        return None
    try:
        return ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, ValueError):
        return None


def resolve_group_zone(*, group_id: int, timezone_name: str | None) -> ZoneInfo:
    """Return the group's zone, falling back to UTC and warning when unusable."""
    zone = resolve_timezone_name(timezone_name)
    if zone is not None:
        return zone
    logger.warning(
        "group.timezone_unresolvable group_id=%s timezone=%r falling_back_to=UTC",
        group_id,
        timezone_name,
    )
    return UTC
