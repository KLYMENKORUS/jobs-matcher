__all__ = ("TheJobVacanciesSearchExtractor",)

import datetime as dt
import typing as t

from app.infrastructure.source.parser.api.schemas.thejob.search import JobSearch
from app.modules.data_extractor.decorators import data_extractor_validation
from app.modules.data_extractor.schemas.search import (
    VacanciesSearchResults,
    VacancySearchItem,
)
from app.shared.utils.logger.decorators import delimit_wrapper

from ....adapters.thejob import TheJobDataExtractorAdapter


class TheJobVacanciesSearchExtractor(TheJobDataExtractorAdapter):

    @delimit_wrapper(
        section="search", obj="vacancies-search-results", detail="data extraction"
    )
    @data_extractor_validation(datatype="search / vacancies-search-results")
    async def __call__(
            self, *,
            query: str,
            max_pages: int | None = None,
            collected_until: dt.datetime | None = None,
    ) -> VacanciesSearchResults:
        self.logger.info(f"[{self.log_labels}] search query: {query}")

        # ------------------------------------------------------------------------ #
        search_results: VacanciesSearchResults = VacanciesSearchResults()
        # ------------------------------------------------------------------------ #

        # ------------------------------------------------------------------------ #
        async for job_search in self._iter_search_pages(query=query, max_pages=max_pages):
            search_results.total = job_search.pagination.count

            for job in job_search.jobs:
                vacancy = self.to_vacancy_main(job=job)

                if self.should_skip_vacancy(
                        posted_at=vacancy.posted_at, collected_until=collected_until
                ):
                    self.logger.info(
                        f"[{self.log_labels}] reached already collected vacancies "
                        f"(page {job_search.pagination.current}), stop paging"
                    )
                    return search_results

                if job.is_active and not job.archived:
                    # the search response already has the full vacancy
                    search_results.results.append(
                        VacancySearchItem(
                            url=vacancy.url,
                            source=vacancy.source,
                            posted_at=vacancy.posted_at,
                            main=vacancy,
                        )
                    )
        # ------------------------------------------------------------------------ #

        self.logger.info(
            f"[{self.log_labels}] collected {len(search_results.results)} vacancies "
            f"(source total: {search_results.total})"
        )
        return search_results

    async def _iter_search_pages(
            self, *, query: str, max_pages: int | None
    ) -> t.AsyncIterator[JobSearch]:
        first_page: JobSearch = await self._extract_search_page(query=query, page=1)
        yield first_page

        last_page: int = first_page.pagination.pages
        if max_pages is not None:
            last_page = min(last_page, max_pages)

        for page in range(2, last_page + 1):
            yield await self._extract_search_page(query=query, page=page)

    async def _extract_search_page(self, *, query: str, page: int) -> JobSearch:
        self.logger.detail(f"[{self.log_labels}] fetch search page {page}")

        return await self.api_client.response_data.job_api.search.get(
            data=(
                await self.api_client.search(query=query, page=page, order_by_date="desc")
            ).json_data
        )
