from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from dishka.integrations.fastapi import DishkaRoute, FromDishka

from unitkeeper_backend.api.dependencies.auth import require_user_id
from unitkeeper_backend.api.schemas.balances import (
    BalanceResponse,
    BalanceTransactionPageResponse,
    BalanceTransactionResponse,
    BalanceTransferResponse,
    CreateTransferRequest,
    TransferCandidateResponse,
    TransferCandidatesResponse,
)
from unitkeeper_backend.api.schemas.common import UserResponse
from unitkeeper_backend.application.balances.service import BalanceService

router = APIRouter(prefix="/balances", tags=["balances"], route_class=DishkaRoute)


@router.get("/me", response_model=BalanceResponse)
async def get_my_balance(
    user_id: int = Depends(require_user_id),
    balance_service: FromDishka[BalanceService] = None,
) -> BalanceResponse:
    balance = await balance_service.get_my_balance(user_id=user_id)
    return BalanceResponse.model_validate(balance, from_attributes=True)


@router.get("/transfer-candidates", response_model=TransferCandidatesResponse)
async def list_transfer_candidates(
    user_id: int = Depends(require_user_id),
    balance_service: FromDishka[BalanceService] = None,
) -> TransferCandidatesResponse:
    candidates = await balance_service.list_transfer_candidates(user_id=user_id)
    return TransferCandidatesResponse(
        candidates=[
            TransferCandidateResponse(
                user=UserResponse.model_validate(item.user, from_attributes=True),
                current_balance=item.current_balance,
            )
            for item in candidates
        ]
    )


@router.post("/transfers", response_model=BalanceTransferResponse, status_code=status.HTTP_201_CREATED)
async def create_transfer(
    request: CreateTransferRequest,
    user_id: int = Depends(require_user_id),
    balance_service: FromDishka[BalanceService] = None,
) -> BalanceTransferResponse:
    transfer = await balance_service.transfer(
        sender_user_id=user_id,
        recipient_user_id=request.recipient_user_id,
        amount=request.amount,
    )
    return BalanceTransferResponse.model_validate(transfer, from_attributes=True)


@router.get("/transactions", response_model=BalanceTransactionPageResponse)
async def list_my_balance_transactions(
    user_id: int = Depends(require_user_id),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    balance_service: FromDishka[BalanceService] = None,
) -> BalanceTransactionPageResponse:
    page = await balance_service.list_my_transactions(user_id=user_id, limit=limit, offset=offset)
    return BalanceTransactionPageResponse(
        items=[BalanceTransactionResponse.model_validate(item, from_attributes=True) for item in page.items],
        total=page.total,
        limit=page.limit,
        offset=page.offset,
        has_more=page.has_more,
    )
