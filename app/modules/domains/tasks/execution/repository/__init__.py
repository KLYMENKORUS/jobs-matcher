__all__ = ("TaskRunRepository",)

import datetime as dt
import typing as t

from sqlalchemy import func, literal, select, update
from sqlalchemy.dialects.postgresql import JSONB

from app.infrastructure.database.crud import BaseCRUD
from app.modules.domains.tasks.execution.models import TaskRun
from app.modules.domains.tasks.execution.schemas import (
    ExecutionException,
    ExecutionTimeframe,
)
from app.shared.utils.enums.tasks import TaskType


class TaskRunRepository(BaseCRUD[TaskRun]):
    model = TaskRun

    # [read]
    # ------------------------------------------------------------------------ #
    async def get_unfinished(self, *, task_type: TaskType) -> TaskRun | None:
        query = (
            select(TaskRun)
            .where(TaskRun.task_type == task_type, TaskRun.completed_at.is_(None))
            .order_by(TaskRun.id.desc())
            .limit(1)
        )
        return await self.session.scalar(query)

    # ------------------------------------------------------------------------ #

    # [write]
    # ------------------------------------------------------------------------ #
    async def set_status(self, *, id: int, status: int) -> None:
        await self.session.execute(
            update(TaskRun).where(TaskRun.id == id).values(execution_status=status)
        )

    async def merge_details(self, *, id: int, details: dict[str, t.Any]) -> None:
        """Shallow-merge keys into `details` (`details || :details`)."""
        await self.session.execute(
            update(TaskRun)
            .where(TaskRun.id == id)
            .values(
                details=TaskRun.details.op("||", return_type=JSONB)(
                    literal(details, JSONB)
                )
            )
        )

    async def push_timeframe(self, *, id: int) -> None:
        timeframe = ExecutionTimeframe(started_at=dt.datetime.now(dt.UTC))
        await self._append_json(
            id=id, column="timeframes", item=timeframe.model_dump(mode="json")
        )

    async def finish_timeframe(self, *, id: int) -> None:
        """Close the last open timeframe (the attempt that is ending)."""
        run: TaskRun | None = await self.get(id=id)
        if run is None or not run.timeframes:
            return

        timeframes: list[dict[str, t.Any]] = list(run.timeframes)
        if timeframes[-1].get("finished_at") is None:
            timeframes[-1] = {
                **timeframes[-1],
                "finished_at": dt.datetime.now(dt.UTC).isoformat(),
            }
            run.timeframes = timeframes
            await self.session.flush()

    async def push_exception(
        self,
        *,
        id: int,
        full_traceback: str,
        short_traceback: str | None = None,
    ) -> None:
        exception = ExecutionException(
            exception_time=dt.datetime.now(dt.UTC),
            short_traceback=short_traceback,
            full_traceback=full_traceback,
        )
        await self._append_json(
            id=id, column="exceptions", item=exception.model_dump(mode="json")
        )

    async def complete(self, *, id: int) -> None:
        await self.session.execute(
            update(TaskRun).where(TaskRun.id == id).values(completed_at=func.now())
        )

    async def _append_json(
        self, *, id: int, column: str, item: dict[str, t.Any]
    ) -> None:
        target = getattr(TaskRun, column)
        await self.session.execute(
            update(TaskRun)
            .where(TaskRun.id == id)
            .values(
                {column: target.op("||", return_type=JSONB)(literal([item], JSONB))}
            )
        )

    # ------------------------------------------------------------------------ #
