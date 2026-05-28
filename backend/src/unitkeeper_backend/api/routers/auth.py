from __future__ import annotations

from fastapi import APIRouter, Depends

from dishka.integrations.fastapi import DishkaRoute, FromDishka

from unitkeeper_backend.api.dependencies.auth import require_user_id
from unitkeeper_backend.api.schemas.auth import SessionResponse, TelegramAuthRequest
from unitkeeper_backend.api.schemas.common import CurrentContextResponse
from unitkeeper_backend.application.auth.service import AuthService
from unitkeeper_backend.application.context.service import CurrentContextService

router = APIRouter(prefix="/auth", tags=["auth"], route_class=DishkaRoute)


@router.post("/telegram", response_model=SessionResponse)
async def authenticate_telegram(
    request: TelegramAuthRequest,
    auth_service: FromDishka[AuthService] = None,
) -> SessionResponse:
    session = await auth_service.authenticate(request.init_data)
    return SessionResponse(
        access_token=session.access_token,
        expires_at=session.expires_at,
        context=CurrentContextResponse.model_validate(session.context, from_attributes=True),
    )


@router.get("/me", response_model=CurrentContextResponse)
async def get_me(
    user_id: int = Depends(require_user_id),
    context_service: FromDishka[CurrentContextService] = None,
) -> CurrentContextResponse:
    context = await context_service.resolve(user_id)
    return CurrentContextResponse.model_validate(context, from_attributes=True)
