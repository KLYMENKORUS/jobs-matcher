__all__ = ("TheJobDataExtractor",)

import datetime as dt

from app.infrastructure.source.parser.api.sources.thejob import TheJobParserRequestClient
from app.modules.data_extractor.schemas.search import VacanciesSearchResults
from app.modules.data_extractor.schemas.vacancy import VacancyMain
from app.shared.utils.logger import Logger, LogLabels

from ..._base.extractor import BaseDataExtractor
from .search import TheJobVacanciesSearchExtractor
from .vacancy import TheJobVacancyMainExtractor


class TheJobDataExtractor(BaseDataExtractor):

    # [search extractor]
    ################################################################################
    class Search(BaseDataExtractor.Search):

        def __init__(
                self, *, logger: Logger, log_labels: LogLabels,
                api_client: TheJobParserRequestClient
        ) -> None:
            # ------------------------------------------------------------------------ #
            self._extract_vacancies = TheJobVacanciesSearchExtractor(
                logger=logger, log_labels=log_labels, api_client=api_client
            )
            # ------------------------------------------------------------------------ #

        async def extract_vacancies(
                self, *,
                query: str,
                max_pages: int | None = None,
                collected_until: dt.datetime | None = None,
        ) -> VacanciesSearchResults:
            return await self._extract_vacancies(
                query=query, max_pages=max_pages, collected_until=collected_until
            )
    ################################################################################

    # [vacancy extractor]
    ################################################################################
    class Vacancy(BaseDataExtractor.Vacancy):

        def __init__(
                self, *, logger: Logger, log_labels: LogLabels,
                api_client: TheJobParserRequestClient
        ) -> None:
            # ------------------------------------------------------------------------ #
            self._extract_main = TheJobVacancyMainExtractor(
                logger=logger, log_labels=log_labels, api_client=api_client
            )
            # ------------------------------------------------------------------------ #

        async def extract_main(self, *, url: str) -> VacancyMain:
            return await self._extract_main(url=url)
    ################################################################################

    def __init__(self, *, logger: Logger) -> None:
        super().__init__(logger=logger)

        # [extractor instance params]
        # ------------------------------------------------------------------------ #
        api_client: TheJobParserRequestClient = \
            TheJobParserRequestClient(logger=logger)
        # ------------------------------------------------------------------------ #

        # [extractors]
        # ------------------------------------------------------------------------ #
        self.search = self.Search(
            logger=logger, log_labels=self.log_labels, api_client=api_client
        )
        # ------------------------------------------------------------------------ #
        self.vacancy = self.Vacancy(
            logger=logger, log_labels=self.log_labels, api_client=api_client
        )
        # ------------------------------------------------------------------------ #
