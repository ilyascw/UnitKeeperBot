from __future__ import annotations

from db.models import User


def test_user_schema_stores_optional_telegram_photo_url() -> None:
    column = User.__table__.c.photo_url

    assert column.nullable is True
