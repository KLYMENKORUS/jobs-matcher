__all__ = ("TheJobDataExtractorAdapter",)

import re
import typing as t
from urllib.parse import urlparse

from app.infrastructure.source.parser.api.schemas.thejob.job import Job
from app.infrastructure.source.parser.api.sources.thejob import TheJobParserRequestClient
from app.modules.data_extractor.schemas.vacancy import (
    VacancyLocation,
    VacancyMain,
    VacancySalary,
)
from app.shared.settings import settings
from app.shared.utils.enums.domains.vacancies import VacancySource
from app.shared.utils.exceptions.source import NotAVacancyUrlError
from app.shared.utils.logger import Logger, LogLabels

from ..._base.adapters import BaseDataExtractorAdapter


class TheJobDataExtractorAdapter(BaseDataExtractorAdapter):

    VACANCIES_PATH: t.Final[str] = "jobs"

    VACANCY_PATH_PATTERN: re.Pattern[str] = (
        re.compile(
            pattern=r"""
                ^/jobs/         # vacancy pages live under /jobs/
                ([^/?#]+)       # captured slug, e.g. python-developer-kyiv-8404258988798199237
                /?$             # optional trailing slash, nothing after
            """,
            flags=re.VERBOSE
        )
    )

    def __init__(
            self, *,
            logger: Logger,
            log_labels: LogLabels,
            api_client: TheJobParserRequestClient
    ) -> None:
        super().__init__(
            logger=logger,
            log_labels=log_labels,
            source=VacancySource.THE_JOB,
            base_url=settings.THE_JOB_URL
        )

        # ------------------------------------------------------------------------ #
        self.api_client: TheJobParserRequestClient = api_client
        # ------------------------------------------------------------------------ #

    def extract_job_slug(self, *, url: str) -> str:
        if (match := self.VACANCY_PATH_PATTERN.search(urlparse(url).path)) is not None:
            return match.group(1)

        raise NotAVacancyUrlError(url=url, source=self.source)

    def build_vacancy_url(self, *, slug: str) -> str:
        return self.concatenate_source_url(url=f"{self.VACANCIES_PATH}/{slug}")

    def to_vacancy_main(self, *, job: Job) -> VacancyMain:
        return VacancyMain(
            url=self.build_vacancy_url(slug=job.slug),
            source=self.source,
            external_id=job.id,
            title=job.title,
            company=job.company_name,
            summary=job.summary,
            description=job.description,
            salary=(
                VacancySalary(
                    min=job.salary_min,
                    currency=job.salary_currency,
                    period=job.salary_period,
                )
                if job.salary_min is not None
                else None
            ),
            locations=[
                VacancyLocation(
                    country=location.country_name,
                    city=location.city_name,
                    work_mode=location.work_mode,
                )
                for location in job.locations
            ],
            is_remote=job.is_remote,
            experience_levels=job.experience_levels,
            employment_types=job.employment_types,
            skills=job.tech_stack,
            posted_at=job.source_posted_at or job.created_at,
        )
