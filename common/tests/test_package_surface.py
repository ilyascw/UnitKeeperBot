from db import (
    Balance,
    BalanceTransaction,
    Base,
    Group,
    GroupMembership,
    GroupMemberWeight,
    IdempotencyKey,
    NotificationDeliveryAttempt,
    NotificationOutboxEvent,
    SprintMemberResult,
    SprintRun,
    Task,
    TaskLog,
    User,
    async_session_maker,
    engine,
    settings,
)


def test_public_package_surface_is_importable() -> None:
    assert Base.metadata.tables
    assert async_session_maker is not None
    assert engine is not None
    assert settings.database_url.startswith("postgresql+asyncpg://")


def test_metadata_contains_shared_schema_models() -> None:
    expected_models = {
        Balance,
        BalanceTransaction,
        Group,
        GroupMemberWeight,
        GroupMembership,
        IdempotencyKey,
        NotificationDeliveryAttempt,
        NotificationOutboxEvent,
        SprintMemberResult,
        SprintRun,
        Task,
        TaskLog,
        User,
    }

    assert {model.__tablename__ for model in expected_models} <= set(Base.metadata.tables)
