__all__ = (
    "TaskRunSchema",
    "ExecutionTimeframe",
    "ExecutionException",
)

import datetime as dt
import typing as t

from pydantic import BaseModel, ConfigDict, Field

from app.shared.utils.enums.tasks import TaskType


class ExecutionTimeframe(BaseModel):
    started_at: dt.datetime
    finished_at: dt.datetime | None = Field(default=None)


class ExecutionException(BaseModel):
    exception_time: dt.datetime
    short_traceback: str | None = Field(default=None)
    full_traceback: str


class TaskRunSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_type: TaskType
    execution_status: int
    details: dict[str, t.Any] = Field(default_factory=dict)
    timeframes: list[ExecutionTimeframe] = Field(default_factory=list)
    exceptions: list[ExecutionException] = Field(default_factory=list)
    created_at: dt.datetime
    completed_at: dt.datetime | None = Field(default=None)
