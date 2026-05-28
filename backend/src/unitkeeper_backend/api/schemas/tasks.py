from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field


class CreateTaskRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    frequency_per_sprint: int = Field(gt=0)
    unit_cost: Decimal = Field(ge=0)


class UpdateTaskRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    frequency_per_sprint: int | None = Field(default=None, gt=0)
    unit_cost: Decimal | None = Field(default=None, ge=0)


class RejectTaskLogRequest(BaseModel):
    reason: str = Field(min_length=1)


class BulkImportTaskItem(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    frequency_per_sprint: int = Field(gt=0)
    unit_cost: Decimal = Field(ge=0)


class BulkImportTasksRequest(BaseModel):
    items: list[BulkImportTaskItem] = Field(min_length=1, max_length=500)


class FrequencyAdjustmentRequest(BaseModel):
    step: int = Field(default=1, gt=0)
