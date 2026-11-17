__all__ = ("ParsingTask",)

import typing as t

from app.infrastructure.database.service import UnitOfWork
from app.modules.data_extractor.factory import DataExtractorFactory
from app.modules.domains.interactions import InteractionService
from app.modules.domains.user_settings.service import UserSettingsService
from app.modules.domains.users import UserService
from app.modules.domains.vacancies import VacancyService
from app.shared.utils.enums.tasks import ParsingExecutionStatus, TaskType
from app.shared.utils.logger import Logger, LogLabels

from ..._base.tasks import BaseProcessingTask
from ..channel import ParsingTelegramChannel

if t.TYPE_CHECKING:
    from ..._base.states import BaseTaskState


class ParsingTask(BaseProcessingTask[ParsingExecutionStatus]):
    """
    Worker 1: collect new vacancies for every unique keyword from every source
    and link them to the users whose keywords found them.

    START -> PREPARE_SEARCH_QUERIES -> COLLECT_VACANCY_URLS
          -> COLLECT_VACANCY_DETAILS -> LINK_VACANCIES_TO_USERS -> COMPLETED
    """

    task_type = TaskType.PARSING
    execution_status_enum = ParsingExecutionStatus

    def __init__(
        self,
        *,
        logger: Logger,
        uow: UnitOfWork,
        celery_details: dict[str, t.Any] | None = None,
    ) -> None:
        super().__init__(
            logger=logger,
            log_labels=LogLabels.PARSING_TASK,
            uow=uow,
            celery_details=celery_details,
        )

        # [services]
        # ------------------------------------------------------------------------ #
        self.vacancy_service: VacancyService = VacancyService(
            uow_factory=self.get_uow
        )
        # ------------------------------------------------------------------------ #
        self.user_settings_service: UserSettingsService = UserSettingsService(
            uow_factory=self.get_uow
        )
        # ------------------------------------------------------------------------ #
        self.user_service: UserService = UserService(uow_factory=self.get_uow)
        # ------------------------------------------------------------------------ #
        self.interaction_service: InteractionService = InteractionService(
            uow_factory=self.get_uow
        )
        # ------------------------------------------------------------------------ #
        self.extractor_factory: DataExtractorFactory = DataExtractorFactory(
            logger=logger
        )
        # ------------------------------------------------------------------------ #

        # [notifications]
        # ------------------------------------------------------------------------ #
        self.tg_channel = ParsingTelegramChannel(logger=logger)
        # ------------------------------------------------------------------------ #

    def get_states(self) -> dict[ParsingExecutionStatus, BaseTaskState]:
        from ..states import ParsingIterableTaskState

        return {
            t.cast(ParsingExecutionStatus, state.execution_status): state
            for state in ParsingIterableTaskState(task=self)
        }
