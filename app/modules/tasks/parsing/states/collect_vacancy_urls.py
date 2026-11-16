import datetime as dt
import itertools
import traceback

from app.modules.data_extractor.schemas.search import VacanciesSearchResults
from app.shared.utils.enums.tasks import ParsingExecutionStatus as ExecutionStatus
from app.shared.utils.logger.decorators import delimit_wrapper

from ..._base.states import BaseTaskState
from ..task import ParsingTask


class ParsingCollectVacancyUrlsState(BaseTaskState):
    """
    Search every (source, keyword) of the run and save what was found.

    A source whose search only lists links gives url (+ posted_at): such vacancies
    are saved as NEW and COLLECT_VACANCY_DETAILS fills them in. A source whose
    search already returns full data saves them as COLLECTED right away.

    Where a search stops is derived from the data itself: `max(posted_at)` of the
    vacancies already linked to that (source, keyword), or N days back for a new
    pair. Each search is saved in one transaction, so after a crash the state is
    simply re-run: searches already saved stop on their first page, the rest
    collect their full period. A failed search is logged and does not stop the
    others; nothing of it is saved, so the next run repeats it.
    """
    task: ParsingTask
    execution_status = ExecutionStatus.COLLECT_VACANCY_URLS

    @delimit_wrapper(
        section="parsing", obj="collect-vacancy-urls",
        detail="search sources by keywords", is_subdelimit=True
    )
    async def run(self) -> None:
        # ------------------------------------------------------------------------ #
        sources: list[str] = self.task.details.get("sources", [])
        keywords: list[str] = self.task.details.get("keywords", [])
        pairs: list[tuple[str, str]] = list(itertools.product(sources, keywords))

        if not pairs:
            return

        collected_until: dict[tuple[str, str], dt.datetime] = (
            await self.task.vacancy_service.get_collected_until(
                sources=sources, keywords=keywords
            )
        )
        # ------------------------------------------------------------------------ #

        new: int = 0
        failed: list[str] = []

        for number, (source, keyword) in enumerate(pairs, start=1):
            self.task.logger.subinfo(
                f"[{self.task.log_labels}] ({number}/{len(pairs)}) {source} / {keyword!r}"
            )
            created: int | None = await self._collect(
                source=source, keyword=keyword,
                collected_until=collected_until[(source, keyword)],
            )
            if created is None:
                failed.append(f"{source}:{keyword}")
            else:
                new += created

        await self.task.merge_details(search={
            "searches": len(pairs), "failed": failed, "new_vacancies": new,
        })
        self.task.logger.info(
            f"[{self.task.log_labels}] searches: {len(pairs)}, failed: {len(failed)}, "
            f"new vacancies: {new}"
        )

    async def _collect(
            self, *, source: str, keyword: str, collected_until: dt.datetime
    ) -> int | None:
        """Returns the number of new vacancies, or None if the search failed."""
        try:
            results: VacanciesSearchResults = (
                await self.task.extractor_factory(source=source).search.extract_vacancies(
                    query=keyword, collected_until=collected_until
                )
            )
            created: int = await self.task.vacancy_service.save_search_results(
                keyword=keyword,
                vacancies=[item.to_create_schema() for item in results.results],
            )
        except Exception:  # noqa
            self.task.logger.error(f"[{self.task.log_labels}] {traceback.format_exc()}")
            return None

        self.task.logger.info(
            f"[{self.task.log_labels}] {source} / {keyword!r}: "
            f"found {len(results.results)}, new {created} "
            f"(since {collected_until:%Y-%m-%d %H:%M})"
        )
        return created
