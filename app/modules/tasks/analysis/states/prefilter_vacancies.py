from collections import defaultdict

from app.modules.domains.interactions import InteractionWithVacancySchema
from app.modules.domains.users import UserSchema
from app.shared.utils.enums.tasks import AnalysisExecutionStatus as ExecutionStatus
from app.shared.utils.logger.decorators import delimit_wrapper

from ..._base.states import BaseTaskState
from ..task import AnalysisTask


class AnalysisPrefilterVacanciesState(BaseTaskState):
    """
    Reject the NEW interactions that are obviously not a fit (see
    VacancyPrefilter) before the AI sees them: NEW -> REJECTED with the reason.

    Only for the users with a prepared CV - the others are not analysed in
    this run anyway. Idempotent: a re-run only checks what is still NEW.
    """
    task: AnalysisTask
    execution_status = ExecutionStatus.PREFILTER_VACANCIES

    @delimit_wrapper(
        section="analysis", obj="prefilter-vacancies",
        detail="reject obvious mismatches without ai", is_subdelimit=True
    )
    async def run(self) -> None:
        cvs: dict[str, str] = self.task.details.get("cvs", {})
        users: list[UserSchema] = [
            user for user in await self.task.user_service.get_active_users()
            if str(user.id) in cvs
        ]

        rejected: int = sum([await self._prefilter_user(user=user) for user in users])

        await self.task.merge_details(prefilter_rejected=rejected)
        self.task.logger.info(f"[{self.task.log_labels}] prefilter rejected: {rejected}")

    async def _prefilter_user(self, *, user: UserSchema) -> int:
        keywords: list[str] = user.settings.keywords if user.settings else []
        interactions: list[InteractionWithVacancySchema] = (
            await self.task.interaction_service.get_new_interactions(
                user_id=user.id, limit=None
            )
        )

        # one update per reason instead of one per interaction
        by_reason: defaultdict[str, list[int]] = defaultdict(list)
        for interaction in interactions:
            if reason := self.task.prefilter.check(
                    vacancy=interaction.vacancy, keywords=keywords
            ):
                by_reason[reason].append(interaction.id)

        rejected: int = sum([
            await self.task.interaction_service.reject(
                interaction_ids=ids, reason=reason
            )
            for reason, ids in by_reason.items()
        ])

        self.task.logger.detail(
            f"[{self.task.log_labels}] user (id: {user.id}): "
            f"prefilter rejected {rejected} of {len(interactions)}"
        )
        return rejected
