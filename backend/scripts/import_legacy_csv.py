from __future__ import annotations

import argparse
import asyncio
import csv
import json
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from db.enums import BalanceTransactionType, TaskLogStatus, Weekday
from db.models import (
    Balance,
    BalanceTransaction,
    Group,
    GroupMembership,
    GroupMemberWeight,
    Task,
    TaskLog,
    User,
)
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from unitkeeper_backend.config import settings
from unitkeeper_backend.infrastructure.auth.session_tokens import HmacSessionTokenManager

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = REPO_ROOT / "data"

WEEKDAYS = {
    "понедельник": Weekday.MONDAY,
    "monday": Weekday.MONDAY,
    "вторник": Weekday.TUESDAY,
    "tuesday": Weekday.TUESDAY,
    "среда": Weekday.WEDNESDAY,
    "wednesday": Weekday.WEDNESDAY,
    "четверг": Weekday.THURSDAY,
    "thursday": Weekday.THURSDAY,
    "пятница": Weekday.FRIDAY,
    "friday": Weekday.FRIDAY,
    "суббота": Weekday.SATURDAY,
    "saturday": Weekday.SATURDAY,
    "воскресенье": Weekday.SUNDAY,
    "sunday": Weekday.SUNDAY,
}


@dataclass(frozen=True)
class LegacyFiles:
    groups: Path
    users: Path
    tasks: Path
    logs: Path
    balances: Path


def find_legacy_files(data_dir: Path) -> LegacyFiles:
    files = list(data_dir.glob("*.csv"))
    by_prefix: dict[str, Path] = {}
    for path in files:
        name = path.name.lower()
        if name.startswith("_groups__"):
            by_prefix["groups"] = path
        elif name.startswith("users_"):
            by_prefix["users"] = path
        elif name.startswith("tasks_"):
            by_prefix["tasks"] = path
        elif name.startswith("logs_"):
            by_prefix["logs"] = path
        elif name.startswith("balances_"):
            by_prefix["balances"] = path

    missing = sorted({"groups", "users", "tasks", "logs", "balances"} - set(by_prefix))
    if missing:
        raise SystemExit(f"Missing CSV files in {data_dir}: {', '.join(missing)}")

    return LegacyFiles(
        groups=by_prefix["groups"],
        users=by_prefix["users"],
        tasks=by_prefix["tasks"],
        logs=by_prefix["logs"],
        balances=by_prefix["balances"],
    )


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as file:
        return [dict(row) for row in csv.DictReader(file)]


def parse_int(value: str | None) -> int | None:
    if value is None or value.strip() == "":
        return None
    return int(value)


def parse_decimal(value: str | None, *, default: str = "0") -> Decimal:
    if value is None or value.strip() == "":
        return Decimal(default)
    try:
        return Decimal(value)
    except InvalidOperation:
        return Decimal(default)


def parse_bool(value: str | None) -> bool:
    if value is None or value.strip() == "":
        return True
    return value.strip().lower() in {"1", "true", "t", "yes", "y"}


def parse_timestamp(value: str | None) -> datetime:
    if value is None or value.strip() == "":
        return datetime.now(UTC)
    return datetime.fromisoformat(value.strip())


def parse_weights(value: str | None) -> dict[int, Decimal]:
    if value is None or value.strip() == "":
        return {}
    raw = json.loads(value)
    return {int(user_id): parse_decimal(str(weight)) for user_id, weight in raw.items()}


def normalize_weekday(value: str | None) -> Weekday:
    if value is None:
        return Weekday.MONDAY
    return WEEKDAYS.get(value.strip().lower(), Weekday.MONDAY)


def normalize_duration(value: str | None) -> int:
    duration = parse_int(value) or 7
    if duration <= 0 or duration % 7 != 0:
        return 7
    return duration


def normalize_frequency(value: str | None) -> int:
    frequency = int(parse_decimal(value, default="1").to_integral_value())
    return max(0, frequency)


# Legacy CSVs carry no names, only Telegram ids - and only real Telegram auth
# ever fills in first_name/username. Dev-seeded users would otherwise render
# as "Участник <id>" everywhere until someone actually logs in as them, so we
# assign a deterministic placeholder name for local testing.
DEV_PLACEHOLDER_NAMES = ["Аня", "Марк", "Соня", "Дима", "Катя", "Женя", "Паша", "Лена"]


async def ensure_user(session: AsyncSession, user_id: int) -> User:
    user = await session.get(User, user_id)
    if user is None:
        user = User(
            id=user_id, first_name=DEV_PLACEHOLDER_NAMES[user_id % len(DEV_PLACEHOLDER_NAMES)]
        )
        session.add(user)
        await session.flush()
    return user


async def upsert_group(session: AsyncSession, row: dict[str, str], owner_user_id: int) -> Group:
    group_id = parse_int(row.get("id"))
    if group_id is None:
        raise ValueError("Group row has no id")

    group = await session.get(Group, group_id)
    if group is None:
        group = Group(id=group_id)
        session.add(group)

    group.name = row["name"]
    group.join_secret = row["password"]
    group.owner_user_id = owner_user_id
    group.sprint_start_weekday = normalize_weekday(row.get("start_day"))
    group.sprint_duration_days = normalize_duration(row.get("sprint_duration"))
    group.timezone = "UTC"
    group.balance = parse_decimal(row.get("group_balance")).quantize(Decimal("0.01"))
    await session.flush()
    return group


async def upsert_membership(
    session: AsyncSession,
    *,
    group_id: int,
    user_id: int,
    weight_percent: Decimal,
) -> None:
    query = select(GroupMembership).where(
        GroupMembership.group_id == group_id,
        GroupMembership.user_id == user_id,
        GroupMembership.left_at.is_(None),
    )
    result = await session.execute(query)
    membership = result.scalar_one_or_none()
    if membership is None:
        membership = GroupMembership(group_id=group_id, user_id=user_id)
        session.add(membership)
        await session.flush()

    weight_result = await session.execute(
        select(GroupMemberWeight).where(GroupMemberWeight.membership_id == membership.id)
    )
    weight = weight_result.scalar_one_or_none()
    if weight is None:
        weight = GroupMemberWeight(membership_id=membership.id, weight_percent=weight_percent)
        session.add(weight)
    else:
        weight.weight_percent = weight_percent
    await session.flush()


async def upsert_task(session: AsyncSession, row: dict[str, str]) -> None:
    task_id = parse_int(row.get("id"))
    group_id = parse_int(row.get("group_id"))
    if task_id is None or group_id is None:
        return

    task = await session.get(Task, task_id)
    if task is None:
        task = Task(id=task_id, group_id=group_id)
        session.add(task)

    task.group_id = group_id
    task.title = row["title"]
    task.frequency_per_sprint = normalize_frequency(row.get("frequency"))
    task.unit_cost = parse_decimal(row.get("cost")).quantize(Decimal("0.01"))
    task.deleted_at = None if parse_bool(row.get("status")) else datetime.now(UTC)
    await session.flush()


async def upsert_task_log(session: AsyncSession, row: dict[str, str]) -> None:
    log_id = parse_int(row.get("id"))
    group_id = parse_int(row.get("group_id"))
    user_id = parse_int(row.get("user_id"))
    task_id = parse_int(row.get("task_id"))
    if log_id is None or group_id is None or user_id is None or task_id is None:
        return

    timestamp = parse_timestamp(row.get("timestamp"))
    raw_status = (row.get("status") or "").strip().lower()
    status = TaskLogStatus.COMPLETED if raw_status == "completed" else TaskLogStatus.PENDING

    log = await session.get(TaskLog, log_id)
    if log is None:
        log = TaskLog(id=log_id)
        session.add(log)

    log.group_id = group_id
    log.task_id = task_id
    log.performer_user_id = user_id
    log.status = status
    log.approver_user_id = None
    log.decided_at = timestamp if status == TaskLogStatus.COMPLETED else None
    log.rejection_reason = None
    log.created_at = timestamp
    log.updated_at = timestamp
    await session.flush()


async def upsert_balance(session: AsyncSession, row: dict[str, str]) -> None:
    # Dev seed data: balances always start at zero. Legacy CSV opening
    # balances are dropped on purpose - only task/log seed state carries over.
    balance_id = parse_int(row.get("id"))
    user_id = parse_int(row.get("user_id"))
    group_id = parse_int(row.get("group_id"))
    if balance_id is None or user_id is None or group_id is None:
        return

    balance = await session.get(Balance, balance_id)
    if balance is None:
        balance = Balance(id=balance_id, user_id=user_id, group_id=group_id)
        session.add(balance)

    balance.user_id = user_id
    balance.group_id = group_id
    balance.current_balance = Decimal("0.00")
    await session.flush()


async def clear_opening_transaction(session: AsyncSession, *, group_id: int, user_id: int) -> None:
    description = "Imported opening balance from legacy CSV"
    query = select(BalanceTransaction).where(
        BalanceTransaction.group_id == group_id,
        BalanceTransaction.user_id == user_id,
        BalanceTransaction.transaction_type == BalanceTransactionType.MANUAL_ADJUSTMENT,
        BalanceTransaction.description == description,
    )
    result = await session.execute(query)
    transaction = result.scalar_one_or_none()
    if transaction is not None:
        await session.delete(transaction)
        await session.flush()


async def reset_sequences(session: AsyncSession) -> None:
    table_names = (
        "groups",
        "group_memberships",
        "group_member_weights",
        "tasks",
        "task_logs",
        "balances",
        "balance_transactions",
        "sprint_runs",
        "sprint_member_results",
    )
    for table_name in table_names:
        await session.execute(
            text(
                f"""
                SELECT setval(
                    pg_get_serial_sequence('{table_name}', 'id'),
                    COALESCE((SELECT MAX(id) FROM {table_name}), 1),
                    (SELECT MAX(id) IS NOT NULL FROM {table_name})
                )
                """
            )
        )


def collect_user_ids(
    *,
    groups: Iterable[dict[str, str]],
    users: Iterable[dict[str, str]],
    logs: Iterable[dict[str, str]],
    balances: Iterable[dict[str, str]],
) -> set[int]:
    user_ids: set[int] = set()
    for row in users:
        user_id = parse_int(row.get("id"))
        if user_id is not None:
            user_ids.add(user_id)
    for row in groups:
        owner_id = parse_int(row.get("owner_id"))
        if owner_id is not None:
            user_ids.add(owner_id)
        user_ids.update(parse_weights(row.get("weights")).keys())
    for row in logs:
        user_id = parse_int(row.get("user_id"))
        if user_id is not None:
            user_ids.add(user_id)
    for row in balances:
        user_id = parse_int(row.get("user_id"))
        if user_id is not None:
            user_ids.add(user_id)
    return user_ids


async def import_legacy_csv(data_dir: Path, database_url: str) -> list[int]:
    files = find_legacy_files(data_dir)
    groups = read_csv(files.groups)
    users = read_csv(files.users)
    tasks = read_csv(files.tasks)
    logs = read_csv(files.logs)
    balances = read_csv(files.balances)

    engine = create_async_engine(database_url)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async with session_maker() as session:
        async with session.begin():
            for user_id in sorted(
                collect_user_ids(groups=groups, users=users, logs=logs, balances=balances)
            ):
                await ensure_user(session, user_id)

            for row in groups:
                group_id = parse_int(row.get("id"))
                if group_id is None:
                    continue
                weights = parse_weights(row.get("weights"))
                owner_user_id = parse_int(row.get("owner_id"))
                if owner_user_id is None and weights:
                    owner_user_id = min(weights)
                if owner_user_id is None:
                    raise ValueError(f"Group {group_id} has no owner_id and no weights")
                await ensure_user(session, owner_user_id)
                await upsert_group(session, row, owner_user_id)

            for row in users:
                user_id = parse_int(row.get("id"))
                group_id = parse_int(row.get("group_id"))
                if user_id is None or group_id is None:
                    continue
                matching_group = next(
                    item for item in groups if parse_int(item.get("id")) == group_id
                )
                weights = parse_weights(matching_group.get("weights"))
                await upsert_membership(
                    session,
                    group_id=group_id,
                    user_id=user_id,
                    weight_percent=weights.get(user_id, Decimal("0")).quantize(Decimal("0.01")),
                )

            for row in tasks:
                await upsert_task(session, row)

            for row in logs:
                await upsert_task_log(session, row)

            for row in balances:
                await upsert_balance(session, row)
                user_id = parse_int(row.get("user_id"))
                group_id = parse_int(row.get("group_id"))
                if user_id is not None and group_id is not None:
                    await clear_opening_transaction(session, group_id=group_id, user_id=user_id)

            await reset_sequences(session)

        imported_user_ids = sorted(
            collect_user_ids(groups=groups, users=users, logs=logs, balances=balances)
        )

    await engine.dispose()
    return imported_user_ids


def print_tokens(user_ids: list[int]) -> None:
    manager = HmacSessionTokenManager(
        secret=settings.session_secret,
        ttl_seconds=settings.session_ttl_seconds,
    )
    issued_at = datetime.now(UTC)
    print("\nSwagger Bearer tokens:")
    for user_id in user_ids:
        token, _ = manager.issue(user_id=user_id, issued_at=issued_at)
        print(f"user_id={user_id} token={token}")


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import legacy UnitKeeper CSV files into v1 DB schema."
    )
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--database-url", default=settings.database_url)
    parser.add_argument("--no-tokens", action="store_true")
    args = parser.parse_args()

    user_ids = await import_legacy_csv(args.data_dir, args.database_url)
    print(f"Imported legacy CSV data from {args.data_dir}")
    print(f"Imported/updated users: {len(user_ids)}")
    if not args.no_tokens:
        print_tokens(user_ids)


if __name__ == "__main__":
    asyncio.run(main())
