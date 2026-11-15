__all__ = ("BaseProcessingTask",)

import abc
import traceback
import typing as t
from enum import IntEnum

from app.infrastructure.database.service import UnitOfWork
from app.modules.domains.tasks.execution import TaskRunSchema, TaskRunService
from app.shared.utils.enums.tasks import TaskType
from app.shared.utils.logger import Logger, LogLabels

from ..lock import TaskAdvisoryLock

if t.TYPE_CHECKING:
    from ..states import BaseTaskState


class BaseProcessingTask[S: IntEnum](abc.ABC):
    """
    State machine over `S` (an IntEnum with START first and COMPLETED last).

    run():
      1. take the advisory lock for `task_type` (another instance running -> skip);
      2. resume the unfinished `task_runs` row of this type or create a new one;
      3. run every state from the persisted `execution_status` up to COMPLETED,
         saving the next status after each state, so a crash resumes from the
         state that failed instead of starting over.

    The task gets an already started UnitOfWork from the celery task and every
    service of the task works through it (`uow_factory=self.get_uow`), so the
    whole run uses one db session.
    """
    task_type: t.ClassVar[TaskType]
    # set as a class attribute by every task, e.g. `= ParsingExecutionStatus`
    execution_status_enum: type[S]

    def __init__(self, *, logger: Logger, log_labels: LogLabels, uow: UnitOfWork) -> None:
        # ------------------------------------------------------------------------ #
        self.logger: Logger = logger
        # ------------------------------------------------------------------------ #
        self.log_labels: LogLabels = log_labels
        # ------------------------------------------------------------------------ #
        self.uow: UnitOfWork = uow
        # ------------------------------------------------------------------------ #
        self.run_service: TaskRunService = TaskRunService(uow_factory=self.get_uow)
        # ------------------------------------------------------------------------ #
        self.task_run: TaskRunSchema | None = None
        # ------------------------------------------------------------------------ #
        self.execution_status: S | None = None
        # ------------------------------------------------------------------------ #

    def get_uow(self) -> UnitOfWork:
        """`uow_factory` for the task's services: always the task's own UnitOfWork."""
        return self.uow

    # [properties]
    ################################################################################
    @property
    def task_run_id(self) -> int:
        if self.task_run is None:
            raise RuntimeError("task run is not initialized")
        return self.task_run.id

    @property
    def details(self) -> dict[str, t.Any]:
        """Run context saved by earlier states (`task_runs.details`)."""
        if self.task_run is None:
            raise RuntimeError("task run is not initialized")
        return self.task_run.details

    @property
    def start_status(self) -> S:
        return self.execution_status_enum["START"]

    @property
    def completed_status(self) -> S:
        return self.execution_status_enum["COMPLETED"]
    ################################################################################

    # [abstract]
    ################################################################################
    @abc.abstractmethod
    def get_states(self) -> dict[S, BaseTaskState]:
        pass
    ################################################################################

    # [hooks]
    ################################################################################
    async def on_completed(self) -> None:  # noqa: B027 - optional hook
        """Called once, when the run reaches COMPLETED."""
    ################################################################################

    async def run(self) -> bool:
        async with TaskAdvisoryLock(task_type=self.task_type) as acquired:
            if not acquired:
                self.logger.warning(
                    f"[{self.log_labels}] {self.task_type} task is already running, skip"
                )
                return False

            return await self._run_locked()

    async def _run_locked(self) -> bool:
        # [init / resume task run]
        # ------------------------------------------------------------------------ #
        self.task_run = await self.run_service.get_or_create(
            task_type=self.task_type, start_status=self.start_status
        )
        self.execution_status = self.execution_status_enum(self.task_run.execution_status)
        self.logger.info(
            f"[{self.log_labels}] task run (id: {self.task_run_id}), "
            f"current execution status: {self.execution_status.name}"
        )
        await self.run_service.start_timeframe(id=self.task_run_id)
        # ------------------------------------------------------------------------ #

        try:
            # ------------------------------------------------------------------------ #
            states: dict[S, BaseTaskState] = self.get_states()

            for raw in range(self.execution_status, self.completed_status):
                execution_status: S = self.execution_status_enum(raw)

                if (state := states.get(execution_status)) is not None:
                    self.logger.subinfo(
                        f"[{self.log_labels}] run state: {execution_status.name}"
                    )
                    await state.run()

                await self.switch_on_next_execution_status()
            # ------------------------------------------------------------------------ #

            return True
        except Exception:
            self.logger.error(f"[{self.log_labels}] {traceback.format_exc()}")
            # the shared session may hold a failed transaction, clear it before writing
            await self.uow.rollback()
            await self.run_service.add_exception(
                id=self.task_run_id,
                full_traceback=traceback.format_exc(),
                short_traceback=traceback.format_exc(limit=1),
            )
            raise
        finally:
            await self.run_service.finish_timeframe(id=self.task_run_id)

            if self.execution_status == self.completed_status:
                await self.on_completed()
                await self.run_service.complete(id=self.task_run_id)
                self.logger.info(
                    f"[{self.log_labels}] task run (id: {self.task_run_id}) completed"
                )

    async def switch_on_next_execution_status(self) -> None:
        if self.execution_status is None:
            raise RuntimeError("execution status is not initialized")

        execution_status: S = self.execution_status_enum(self.execution_status + 1)
        self.execution_status = execution_status
        await self.run_service.set_status(id=self.task_run_id, status=execution_status)

    async def merge_details(self, **details: t.Any) -> None:
        await self.run_service.merge_details(id=self.task_run_id, details=details)
        # keep the in-memory copy in sync, later states of this run read it
        if self.task_run is not None:
            self.task_run.details = {**self.task_run.details, **details}
