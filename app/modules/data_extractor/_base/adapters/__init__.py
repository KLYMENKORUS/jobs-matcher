__all__ = ("BaseDataExtractorAdapter",)

import datetime as dt

from app.shared.utils.enums.domains.vacancies import VacancySource
from app.shared.utils.logger import Logger, LogLabels


class BaseDataExtractorAdapter:
    """Shared state and helpers for every source's extractors."""

    def __init__(
            self, *,
            logger: Logger,
            log_labels: LogLabels,
            source: VacancySource,
            base_url: str
    ) -> None:
        # ------------------------------------------------------------------------ #
        self.base_url: str = base_url
        # ------------------------------------------------------------------------ #
        self.logger: Logger = logger
        # ------------------------------------------------------------------------ #
        self.log_labels: LogLabels = log_labels
        # ------------------------------------------------------------------------ #
        self.source: VacancySource = source
        # ------------------------------------------------------------------------ #

    def concatenate_source_url(self, *, url: str) -> str:
        return f"{self.base_url}/{url.strip().lstrip('/')}"

    @staticmethod
    def should_skip_vacancy(
            *,
            posted_at: dt.datetime | None,
            collected_until: dt.datetime | None
    ) -> bool:
        """True if the vacancy is not newer than the last collection run."""
        if collected_until is None or posted_at is None:
            return False

        if posted_at.tzinfo is None:
            posted_at = posted_at.replace(tzinfo=dt.UTC)

        if collected_until.tzinfo is None:
            collected_until = collected_until.replace(tzinfo=dt.UTC)

        return posted_at <= collected_until
