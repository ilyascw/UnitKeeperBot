from __future__ import annotations

import enum

from sqlalchemy import Enum


def pg_enum(enum_class: type[enum.Enum], *, name: str | None = None) -> Enum:
    return Enum(
        enum_class,
        name=name or enum_class.__name__.lower(),
        native_enum=True,
        validate_strings=True,
        values_callable=lambda members: [member.value for member in members],
    )
