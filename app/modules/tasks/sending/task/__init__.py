__all__ = ("SendingTask",)

import typing as t

from app.infrastructure.database.service import UnitOfWork
from app.modules.domains.interactions import InteractionService
from app.modules.domains.users import UserService
from app.shared.utils.enums.tasks import SendingExecutionStatus, TaskType
from app.shared.utils.logger import Logger, LogLabels

from ..._base.tasks import BaseProcessingTask
from ..channel import SendingTelegramChannel

if t.TYPE_CHECKING:
    from ..._base.states import BaseTaskState


class SendingTask(BaseProcessingTask[SendingExecutionStatus]):
    """
    Worker 3: send scored vacancies (PENDING, score >= user's min_score) to Telegram.

    START -> SEND_MATCHES -> COMPLETED

    Each interaction is switched to SENT right after its message is delivered,
    so a restarted run never sends the same vacancy twice.
    """
    task_type = TaskType.SENDING
    execution_status_enum = SendingExecutionStatus

    def __init__(
            self, *,
            logger: Logger,
            uow: UnitOfWork,
            celery_details: dict[str, t.Any] | None = None
    ) -> None:
        super().__init__(
            logger=logger, log_labels=LogLabels.SENDING_TASK,
            uow=uow, celery_details=celery_details
        )

        # [services]
        # ------------------------------------------------------------------------ #
        self.user_service: UserService = UserService(uow_factory=self.get_uow)
        # ------------------------------------------------------------------------ #
        self.interaction_service: InteractionService = (
            InteractionService(uow_factory=self.get_uow)
        )
        # ------------------------------------------------------------------------ #

        # [notifications]
        # ------------------------------------------------------------------------ #
        self.tg_channel = SendingTelegramChannel(logger=logger)
        # ------------------------------------------------------------------------ #

    def get_states(self) -> dict[SendingExecutionStatus, BaseTaskState]:
        from ..states import SendingIterableTaskState

        return {
            t.cast(SendingExecutionStatus, state.execution_status): state
            for state in SendingIterableTaskState(task=self)
        }
