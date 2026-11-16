import traceback

from app.modules.data_extractor.schemas.vacancy import VacancyMain
from app.modules.domains.vacancies import VacancySchema
from app.shared.utils.enums.domains.vacancies import VacancyStatus
from app.shared.utils.enums.tasks import ParsingExecutionStatus as ExecutionStatus
from app.shared.utils.logger.decorators import delimit_wrapper

from ..._base.states import BaseTaskState
from ..task import ParsingTask


class ParsingCollectVacancyDetailsState(BaseTaskState):
    """
    Collect the details of every NEW vacancy (only its url is known yet).

    Progress is the vacancy status itself: each vacancy becomes COLLECTED (or
    FAILED) and is committed right away, so a re-run after a crash continues
    with the vacancies that are still NEW. Not limited to this run: NEW
    vacancies left by an earlier run are picked up too.
    """
    task: ParsingTask
    execution_status = ExecutionStatus.COLLECT_VACANCY_DETAILS

    @delimit_wrapper(
        section="parsing", obj="collect-vacancy-details",
        detail="collect details of new vacancies", is_subdelimit=True
    )
    async def run(self) -> None:
        sources: list[str] = [
            str(source) for source in self.task.extractor_factory.available_sources()
        ]

        vacancies: list[VacancySchema] = (
            await self.task.vacancy_service.get_by_status(
                status=VacancyStatus.NEW, sources=sources, limit=None
            )
        )
        self.task.logger.info(f"[{self.task.log_labels}] new vacancies: {len(vacancies)}")

        results: list[bool] = [
            await self._collect(vacancy=vacancy) for vacancy in vacancies
        ]
        collected: int = sum(results)
        failed: int = len(results) - collected

        await self.task.merge_details(
            details={"collected": collected, "failed": failed}
        )
        self.task.logger.info(
            f"[{self.task.log_labels}] vacancy details: collected {collected}, failed {failed}"
        )

    async def _collect(self, *, vacancy: VacancySchema) -> bool:
        try:
            main: VacancyMain = (
                await self.task.extractor_factory(source=vacancy.source).vacancy.extract_main(
                    url=vacancy.url
                )
            )
            await self.task.vacancy_service.save_details(
                vacancy_id=vacancy.id, details=main.to_create_schema()
            )
        except Exception:
            self.task.logger.error(
                f"[{self.task.log_labels}] vacancy (id: {vacancy.id}) {vacancy.url}: "
                f"details collection failed\n{traceback.format_exc()}"
            )
            await self.task.vacancy_service.mark_failed(vacancy_id=vacancy.id)
            return False

        return True
