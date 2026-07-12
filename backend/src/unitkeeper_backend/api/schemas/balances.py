from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from unitkeeper_backend.api.schemas.common import UserResponse


class CreateTransferRequest(BaseModel):
    recipient_user_id: int = Field(gt=0)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)


class BalanceResponse(BaseModel):
    group_id: int
    user_id: int
    current_balance: Decimal


class TransferCandidateResponse(BaseModel):
    user: UserResponse
    current_balance: Decimal


class TransferCandidatesResponse(BaseModel):
    candidates: list[TransferCandidateResponse]


class BalanceTransferResponse(BaseModel):
    group_id: int
    sender_user_id: int
    recipient_user_id: int
    amount: Decimal
    sender_balance: Decimal
    recipient_balance: Decimal


class BalanceTransactionResponse(BaseModel):
    id: int
    group_id: int
    user_id: int
    transaction_type: str
    amount_delta: Decimal
    counterparty_user_id: int | None
    description: str | None
    created_at: datetime


class BalanceTransactionPageResponse(BaseModel):
    items: list[BalanceTransactionResponse]
    total: int
    limit: int
    offset: int
    has_more: bool
