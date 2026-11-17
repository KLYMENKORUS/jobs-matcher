__all__ = ("AnalysisTask",)

import typing as t

from app.infrastructure.database.service import UnitOfWork
from app.modules.analyzer import VacancyMatchAnalyzer
from app.modules.analyzer.prefilter import VacancyPrefilter
from app.modules.cv_parser import CVParser
from app.modules.domains.interactions import InteractionService
from app.modules.domains.users import UserService
from app.shared.utils.enums.tasks import AnalysisExecutionStatus, TaskType
from app.shared.utils.logger import Logger, LogLabels

from ..._base.tasks import BaseProcessingTask
from ..channel import AnalysisTelegramChannel

if t.TYPE_CHECKING:
    from ..._base.states import BaseTaskState


class AnalysisTask(BaseProcessingTask[AnalysisExecutionStatus]):
    """
    Worker 2: score new vacancies against every active user's CV.

    START -> PREPARE_CVS -> PREFILTER_VACANCIES -> ANALYZE_VACANCIES -> COMPLETED

    Works on the interactions the parsing linked to users (status NEW):
      - PREPARE_CVS: parse + clean each CV once, snapshot it to details;
      - PREFILTER_VACANCIES: obvious mismatches -> REJECTED without the AI;
      - ANALYZE_VACANCIES: the AI scores the rest -> PENDING or REJECTED.
    Every state only touches what is still NEW, so a restarted run continues.
    """

    task_type = TaskType.ANALYSIS
    execution_status_enum = AnalysisExecutionStatus

    # the CV goes with every vacancy: keep it short
    MAX_CV_CHARS: t.ClassVar[int] = 4000

    def __init__(
        self,
        *,
        logger: Logger,
        uow: UnitOfWork,
        analyzer: VacancyMatchAnalyzer | None = None,
        celery_details: dict[str, t.Any] | None = None,
    ) -> None:
        super().__init__(
            logger=logger,
            log_labels=LogLabels.ANALYSIS_TASK,
            uow=uow,
            celery_details=celery_details,
        )

        # [services]
        # ------------------------------------------------------------------------ #
        self.user_service: UserService = UserService(uow_factory=self.get_uow)
        # ------------------------------------------------------------------------ #
        self.interaction_service: InteractionService = InteractionService(
            uow_factory=self.get_uow
        )
        # ------------------------------------------------------------------------ #
        self.analyzer: VacancyMatchAnalyzer = analyzer or VacancyMatchAnalyzer()
        # ------------------------------------------------------------------------ #
        self.cv_parser: CVParser = CVParser()
        # ------------------------------------------------------------------------ #
        self.prefilter: VacancyPrefilter = VacancyPrefilter()
        # ------------------------------------------------------------------------ #

        # [notifications]
        # ------------------------------------------------------------------------ #
        self.tg_channel = AnalysisTelegramChannel(logger=logger)
        # ------------------------------------------------------------------------ #

    def get_states(self) -> dict[AnalysisExecutionStatus, BaseTaskState]:
        from ..states import AnalysisIterableTaskState

        return {
            t.cast(AnalysisExecutionStatus, state.execution_status): state
            for state in AnalysisIterableTaskState(task=self)
        }
