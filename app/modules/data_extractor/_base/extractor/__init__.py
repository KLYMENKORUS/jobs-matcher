__all__ = ("BaseDataExtractor",)

import abc
import datetime as dt

from app.modules.data_extractor.schemas.search import VacanciesSearchResults
from app.modules.data_extractor.schemas.vacancy import VacancyMain
from app.shared.utils.descriptors import RequiredTypedField
from app.shared.utils.logger import Logger, LogLabels


class BaseDataExtractor:
    """One per source: groups the source's extractors behind a common interface."""

    # [search extractor]
    ################################################################################
    class Search(abc.ABC):

        @abc.abstractmethod
        async def extract_vacancies(
                self, *,
                query: str,
                max_pages: int | None = None,
                collected_until: dt.datetime | None = None,
        ) -> VacanciesSearchResults:
            pass
    ################################################################################

    # [vacancy extractor]
    ################################################################################
    class Vacancy(abc.ABC):

        @abc.abstractmethod
        async def extract_main(self, *, url: str) -> VacancyMain:
            pass
    ################################################################################

    search = RequiredTypedField(expected_type=Search)
    vacancy = RequiredTypedField(expected_type=Vacancy)

    def __init__(self, *, logger: Logger) -> None:
        # ------------------------------------------------------------------------ #
        self.logger: Logger = logger
        # ------------------------------------------------------------------------ #
        self.log_labels: LogLabels = LogLabels.DATA_EXTRACTOR
        # ------------------------------------------------------------------------ #
