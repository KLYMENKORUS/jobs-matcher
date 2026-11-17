__all__ = ("TaskRun",)

import typing as t
from datetime import datetime

from sqlalchemy import DateTime, Enum, Index, Integer, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base
from app.shared.utils.enums.tasks import TaskType


class TaskRun(Base):
    """
    One execution of a background task (parsing / analysis / sending).

    `execution_status` is the state the run is on; a run is unfinished until
    `completed_at` is set, and the next start of the same task type picks it up.
    """

    __tablename__ = "task_runs"
    __table_args__ = (
        Index("ix_task_runs_task_type_completed_at", "task_type", "completed_at"),
    )

    # [columns]
    ################################################################################
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_type: Mapped[TaskType] = mapped_column(
        Enum(
            TaskType,
            name="task_type",
            values_callable=lambda enum: [member.value for member in enum],
        )
    )
    execution_status: Mapped[int] = mapped_column(Integer)
    details: Mapped[dict[str, t.Any]] = mapped_column(
        JSONB, default=dict, server_default="{}"
    )
    timeframes: Mapped[list[dict[str, t.Any]]] = mapped_column(
        JSONB, default=list, server_default="[]"
    )
    exceptions: Mapped[list[dict[str, t.Any]]] = mapped_column(
        JSONB, default=list, server_default="[]"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ################################################################################
