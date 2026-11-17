import traceback

from app.modules.domains.interactions import (
    InteractionWithVacancySchema,
    VacancyMatchSchema,
)
from app.modules.domains.users import UserSchema
from app.shared.utils.enums.tasks import (
    AnalysisExecutionStatus as ExecutionStatus,
)
from app.shared.utils.logger.decorators import delimit_wrapper

from ..._base.states import BaseTaskState
from ..task import AnalysisTask


class AnalysisAnalyzeVacanciesState(BaseTaskState):
    """
    For every user with a prepared CV: score each NEW interaction left after
    the prefilter and move it to PENDING with the score.

    The user's min_score is not applied here but at sending time: a scored
    vacancy stays PENDING, so lowering min_score later sends the vacancies
    that now pass without asking the AI again.

    Duplicates: the same vacancy is often posted on several sources. If the
    user already has a scored vacancy with the same title + company, its score
    is copied (NEW -> PENDING) instead of asking the AI; the copy is sent too,
    so the user gets the vacancy from every source. Each score is committed
    right away, so a twin analysed earlier in the same run is found too.

    Progress is the interaction status: every score is committed on its own, so
    a crash loses at most the one in flight and a re-run continues with what is
    still NEW. An interaction the AI failed on stays NEW, is skipped for the
    rest of this run and retried by the next one.
    """

    task: AnalysisTask
    execution_status = ExecutionStatus.ANALYZE_VACANCIES

    @delimit_wrapper(
        section="analysis",
        obj="analyze-vacancies",
        detail="score vacancies for users",
        is_subdelimit=True,
    )
    async def run(self) -> None:
        cvs: dict[str, str] = self.task.details.get("cvs", {})
        users: list[UserSchema] = [
            user
            for user in await self.task.user_service.get_active_users()
            if str(user.id) in cvs
        ]
        self.task.logger.info(
            f"[{self.task.log_labels}] users to analyse: {len(users)}"
        )

        totals: dict[str, int] = {"analyzed": 0, "duplicates": 0, "failed": 0}
        for user in users:
            result: dict[str, int] = await self._analyze_user(
                user=user, cv=cvs[str(user.id)]
            )
            totals = {key: totals[key] + result[key] for key in totals}

        await self.task.merge_details(**totals)

    async def _analyze_user(self, *, user: UserSchema, cv: str) -> dict[str, int]:
        interactions: list[
            InteractionWithVacancySchema
        ] = await self.task.interaction_service.get_new_interactions(
            user_id=user.id, limit=None
        )
        results: list[str] = [
            await self._process(user=user, cv=cv, interaction=interaction)
            for interaction in interactions
        ]

        result: dict[str, int] = {
            key: results.count(key) for key in ("analyzed", "duplicates", "failed")
        }
        self.task.logger.info(
            f"[{self.task.log_labels}] user (id: {user.id}): {result}"
        )

        return result

    async def _process(
        self,
        *,
        user: UserSchema,
        cv: str,
        interaction: InteractionWithVacancySchema,
    ) -> str:
        """Twin's score if there is one, otherwise the AI; returns the counter key."""
        if await self.task.interaction_service.copy_twin_match(
            interaction=interaction
        ):
            return "duplicates"

        if await self._analyze_interaction(
            user=user, cv=cv, interaction=interaction
        ):
            return "analyzed"

        return "failed"

    async def _analyze_interaction(
        self,
        *,
        user: UserSchema,
        cv: str,
        interaction: InteractionWithVacancySchema,
    ) -> bool:
        """False if the AI failed: the interaction stays NEW."""
        try:
            match: VacancyMatchSchema = await self.task.analyzer.analyze(
                cv_text=cv, vacancy=interaction.vacancy
            )
        except Exception:  # noqa
            self.task.logger.error(
                f"[{self.task.log_labels}] vacancy (id: {interaction.vacancy_id}) "
                f"analysis failed\n{traceback.format_exc()}"
            )
            return False

        await self.task.interaction_service.set_match(
            interaction_id=interaction.id, match=match
        )
        self.task.logger.detail(
            f"[{self.task.log_labels}] user (id: {user.id}) / "
            f"vacancy (id: {interaction.vacancy_id}): score {match.match_score:.0f}"
        )
        return True
