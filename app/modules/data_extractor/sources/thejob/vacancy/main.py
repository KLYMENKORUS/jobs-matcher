__all__ = ("TheJobVacancyMainExtractor",)

from app.infrastructure.source.parser.api.schemas.thejob.job import Job
from app.modules.data_extractor.decorators import data_extractor_validation
from app.modules.data_extractor.schemas.vacancy import VacancyMain
from app.shared.utils.logger.decorators import delimit_wrapper

from ....adapters.thejob import TheJobDataExtractorAdapter


class TheJobVacancyMainExtractor(TheJobDataExtractorAdapter):

    @delimit_wrapper(
        section="vacancy", obj="main data", detail="data extraction"
    )
    @data_extractor_validation(datatype="vacancy / main data")
    async def __call__(self, *, url: str) -> VacancyMain:
        self.logger.info(f"[{self.log_labels}] vacancy url: {url}")

        # ------------------------------------------------------------------------ #
        slug: str = self.extract_job_slug(url=url)

        job: Job = await self.api_client.response_data.job_api.job_details.get(
            data=(await self.api_client.job_details(job_id=slug)).json_data
        )
        # ------------------------------------------------------------------------ #

        return self.to_vacancy_main(job=job)
