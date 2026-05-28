from __future__ import annotations

from fastapi import APIRouter, Depends

from dishka.integrations.fastapi import DishkaRoute, FromDishka

from unitkeeper_backend.api.dependencies.auth import require_user_id
from unitkeeper_backend.api.routers.tasks import require_group_id
from unitkeeper_backend.api.schemas.common import SprintRunResponse, TempResultsResponse
from unitkeeper_backend.application.sprints.service import SprintService

router = APIRouter(prefix="/sprints", tags=["sprints"], route_class=DishkaRoute)


@router.get("/current/results", response_model=TempResultsResponse)
async def get_temp_results(
    user_id: int = Depends(require_user_id),
    group_id: int = Depends(require_group_id),
    sprint_service: FromDishka[SprintService] = None,
) -> TempResultsResponse:
    results = await sprint_service.get_temp_results(user_id=user_id, group_id=group_id)
    return TempResultsResponse.model_validate(results, from_attributes=True)


@router.post("/current/close", response_model=SprintRunResponse)
async def close_current_sprint(
    group_id: int = Depends(require_group_id),
    sprint_service: FromDishka[SprintService] = None,
) -> SprintRunResponse:
    sprint_run = await sprint_service.close_current_sprint(group_id=group_id)
    return SprintRunResponse.model_validate(sprint_run, from_attributes=True)
