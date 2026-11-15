__all__ = ("TaskRunService",)

import typing as t

from app.infrastructure.database.service import UnitOfWork
from app.modules.domains.tasks.execution.models import TaskRun
from app.modules.domains.tasks.execution.schemas import TaskRunSchema
from app.shared.utils.enums.tasks import TaskType


class TaskRunService:

    def __init__(self, *, uow_factory: t.Callable[[], UnitOfWork] = UnitOfWork) -> None:
        # ------------------------------------------------------------------------ #
        self._uow_factory: t.Callable[[], UnitOfWork] = uow_factory
        # ------------------------------------------------------------------------ #

    # [read]
    ################################################################################
    async def get(self, *, id: int) -> TaskRunSchema | None:
        async with self._uow_factory() as uow:
            run: TaskRun | None = await uow.task_runs.get(id=id)
            return TaskRunSchema.model_validate(run) if run else None

    async def get_or_create(self, *, task_type: TaskType, start_status: int) -> TaskRunSchema:
        """Resume the unfinished run of this task type or start a new one."""
        async with self._uow_factory() as uow:
            run: TaskRun | None = await uow.task_runs.get_unfinished(task_type=task_type)
            if run is None:
                run = await uow.task_runs.create(
                    task_type=task_type, execution_status=start_status,
                    details={}, timeframes=[], exceptions=[]
                )
                await uow.commit()

            return TaskRunSchema.model_validate(run)
    ################################################################################

    # [write]
    ################################################################################
    async def set_status(self, *, id: int, status: int) -> None:
        async with self._uow_factory() as uow:
            await uow.task_runs.set_status(id=id, status=status)
            await uow.commit()

    async def merge_details(self, *, id: int, details: dict[str, t.Any]) -> None:
        async with self._uow_factory() as uow:
            await uow.task_runs.merge_details(id=id, details=details)
            await uow.commit()

    async def start_timeframe(self, *, id: int) -> None:
        async with self._uow_factory() as uow:
            await uow.task_runs.push_timeframe(id=id)
            await uow.commit()

    async def finish_timeframe(self, *, id: int) -> None:
        async with self._uow_factory() as uow:
            await uow.task_runs.finish_timeframe(id=id)
            await uow.commit()

    async def add_exception(
            self, *, id: int, full_traceback: str, short_traceback: str | None = None
    ) -> None:
        async with self._uow_factory() as uow:
            await uow.task_runs.push_exception(
                id=id, full_traceback=full_traceback, short_traceback=short_traceback
            )
            await uow.commit()

    async def complete(self, *, id: int) -> None:
        async with self._uow_factory() as uow:
            await uow.task_runs.complete(id=id)
            await uow.commit()
    ################################################################################
