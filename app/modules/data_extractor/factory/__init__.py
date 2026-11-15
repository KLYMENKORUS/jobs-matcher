__all__ = ("DataExtractorFactory",)

from app.shared.utils.enums.domains.vacancies import VacancySource
from app.shared.utils.exceptions.source import SourceDataExtractorNotFoundError
from app.shared.utils.logger import Logger

from .._base.extractor import BaseDataExtractor
from ..sources.thejob import TheJobDataExtractor


class DataExtractorFactory:
    """Source -> extractor; a new source only has to be registered here."""

    EXTRACTORS = {
        VacancySource.THE_JOB: TheJobDataExtractor,
    }

    def __init__(self, *, logger: Logger) -> None:
        # ------------------------------------------------------------------------ #
        self._logger: Logger = logger
        # ------------------------------------------------------------------------ #
        self._instances: dict[VacancySource, BaseDataExtractor] = {}
        # ------------------------------------------------------------------------ #

    @classmethod
    def available_sources(cls) -> list[VacancySource]:
        return list(cls.EXTRACTORS)

    def __call__(self, *, source: VacancySource | str) -> BaseDataExtractor:
        source = VacancySource(source)

        if (extractor := self._instances.get(source)) is not None:
            return extractor

        if (extractor_cls := self.EXTRACTORS.get(source)) is None:
            raise SourceDataExtractorNotFoundError(source=source)

        self._instances[source] = extractor = extractor_cls(logger=self._logger)
        return extractor
