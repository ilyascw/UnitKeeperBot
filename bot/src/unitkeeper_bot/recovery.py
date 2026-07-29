"""Minimal, non-business fallback responses for temporary Mini App failures."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RecoveryReply:
    text: str
    miniapp_path: str
    retry_after_seconds: int | None = None


def miniapp_unavailable() -> RecoveryReply:
    return RecoveryReply(
        text=(
            "Мини-приложение временно недоступно. "
            "Попробуйте открыть его ещё раз через несколько минут."
        ),
        miniapp_path="/",
        retry_after_seconds=60,
    )


def unsupported_legacy_command() -> RecoveryReply:
    return RecoveryReply(
        text="Эта команда теперь доступна в мини-приложении UnitKeeper.",
        miniapp_path="/",
    )


def owner_handover_required() -> RecoveryReply:
    """A prompt only; ownership selection remains a backend-owned Mini App flow."""
    return RecoveryReply(
        text="Перед выходом владельцу нужно передать управление группой в мини-приложении.",
        miniapp_path="/group",
    )
