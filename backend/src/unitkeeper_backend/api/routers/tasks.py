from __future__ import annotations

from fastapi import APIRouter, Depends, status

from dishka.integrations.fastapi import DishkaRoute, FromDishka, inject

from unitkeeper_backend.api.dependencies.auth import require_user_id
from unitkeeper_backend.api.schemas.common import TaskLogResponse, TaskResponse
from unitkeeper_backend.api.schemas.tasks import (
    BulkImportTasksRequest,
    CreateTaskRequest,
    FrequencyAdjustmentRequest,
    RejectTaskLogRequest,
    UpdateTaskRequest,
)
from unitkeeper_backend.application.context.service import CurrentContextService
from unitkeeper_backend.application.tasks.service import TaskImportItem, TaskService
from unitkeeper_backend.domain.errors import NotFoundError

router = APIRouter(tags=["tasks"], route_class=DishkaRoute)


@inject
async def require_group_id(
    user_id: int = Depends(require_user_id),
    context_service: FromDishka[CurrentContextService] = None,
) -> int:
    context = await context_service.resolve(user_id)
    if context.group is None:
        raise NotFoundError("User has no active group")
    return context.group.id


@router.get("/tasks", response_model=list[TaskResponse])
async def list_tasks(
    group_id: int = Depends(require_group_id),
    task_service: FromDishka[TaskService] = None,
) -> list[TaskResponse]:
    tasks = await task_service.list_tasks(group_id=group_id)
    return [TaskResponse.model_validate(task, from_attributes=True) for task in tasks]


@router.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    request: CreateTaskRequest,
    group_id: int = Depends(require_group_id),
    task_service: FromDishka[TaskService] = None,
) -> TaskResponse:
    task = await task_service.create_task(
        group_id=group_id,
        title=request.title,
        frequency_per_sprint=request.frequency_per_sprint,
        unit_cost=request.unit_cost,
    )
    return TaskResponse.model_validate(task, from_attributes=True)


@router.post("/tasks/import", response_model=list[TaskResponse], status_code=status.HTTP_201_CREATED)
async def import_tasks(
    request: BulkImportTasksRequest,
    group_id: int = Depends(require_group_id),
    task_service: FromDishka[TaskService] = None,
) -> list[TaskResponse]:
    items = [
        TaskImportItem(
            title=item.title,
            frequency_per_sprint=item.frequency_per_sprint,
            unit_cost=item.unit_cost,
        )
        for item in request.items
    ]
    created = await task_service.import_tasks(group_id=group_id, items=items)
    return [TaskResponse.model_validate(task, from_attributes=True) for task in created]


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    group_id: int = Depends(require_group_id),
    task_service: FromDishka[TaskService] = None,
) -> TaskResponse:
    task = await task_service.get_task(group_id=group_id, task_id=task_id)
    return TaskResponse.model_validate(task, from_attributes=True)


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    request: UpdateTaskRequest,
    group_id: int = Depends(require_group_id),
    task_service: FromDishka[TaskService] = None,
) -> TaskResponse:
    task = await task_service.update_task(
        group_id=group_id,
        task_id=task_id,
        title=request.title,
        frequency_per_sprint=request.frequency_per_sprint,
        unit_cost=request.unit_cost,
    )
    return TaskResponse.model_validate(task, from_attributes=True)


@router.post("/tasks/{task_id}/increase-frequency", response_model=TaskResponse)
async def increase_task_frequency(
    task_id: int,
    request: FrequencyAdjustmentRequest | None = None,
    group_id: int = Depends(require_group_id),
    task_service: FromDishka[TaskService] = None,
) -> TaskResponse:
    step = request.step if request is not None else 1
    task = await task_service.adjust_frequency(group_id=group_id, task_id=task_id, delta=step)
    return TaskResponse.model_validate(task, from_attributes=True)


@router.post("/tasks/{task_id}/decrease-frequency", response_model=TaskResponse)
async def decrease_task_frequency(
    task_id: int,
    request: FrequencyAdjustmentRequest | None = None,
    group_id: int = Depends(require_group_id),
    task_service: FromDishka[TaskService] = None,
) -> TaskResponse:
    step = request.step if request is not None else 1
    task = await task_service.adjust_frequency(group_id=group_id, task_id=task_id, delta=-step)
    return TaskResponse.model_validate(task, from_attributes=True)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    group_id: int = Depends(require_group_id),
    task_service: FromDishka[TaskService] = None,
) -> None:
    await task_service.delete_task(group_id=group_id, task_id=task_id)


@router.post("/tasks/{task_id}/done", response_model=TaskLogResponse)
async def mark_task_done(
    task_id: int,
    user_id: int = Depends(require_user_id),
    group_id: int = Depends(require_group_id),
    task_service: FromDishka[TaskService] = None,
) -> TaskLogResponse:
    log = await task_service.mark_done(group_id=group_id, performer_user_id=user_id, task_id=task_id)
    return TaskLogResponse.model_validate(log, from_attributes=True)


@router.post("/task-logs/{log_id}/approve", response_model=TaskLogResponse)
async def approve_task_log(
    log_id: int,
    user_id: int = Depends(require_user_id),
    group_id: int = Depends(require_group_id),
    task_service: FromDishka[TaskService] = None,
) -> TaskLogResponse:
    log = await task_service.approve(group_id=group_id, approver_user_id=user_id, log_id=log_id)
    return TaskLogResponse.model_validate(log, from_attributes=True)


@router.post("/task-logs/{log_id}/reject", response_model=TaskLogResponse)
async def reject_task_log(
    log_id: int,
    request: RejectTaskLogRequest,
    user_id: int = Depends(require_user_id),
    group_id: int = Depends(require_group_id),
    task_service: FromDishka[TaskService] = None,
) -> TaskLogResponse:
    log = await task_service.reject(
        group_id=group_id,
        approver_user_id=user_id,
        log_id=log_id,
        rejection_reason=request.reason,
    )
    return TaskLogResponse.model_validate(log, from_attributes=True)
