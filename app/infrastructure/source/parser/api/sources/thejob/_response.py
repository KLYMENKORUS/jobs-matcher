__all__ = ("TheJobApiResponseData",)

import typing as t

from app.shared.utils.requests.decorators import source_api_wrapper_error

from ...schemas.thejob.job import Job
from ...schemas.thejob.search import JobSearch


class JobApiResponseData:
    # [search]
    ################################################################################
    class Search:
        @classmethod
        @source_api_wrapper_error(source="thejob", api="job-api", path="search")
        async def get(cls, *, data: t.Any) -> JobSearch:
            return JobSearch(**data)

    ################################################################################

    # [details]
    ################################################################################
    class JobDetails:
        @classmethod
        @source_api_wrapper_error(source="thejob", api="job-api", path="job-details")
        async def get(cls, *, data: t.Any) -> Job:
            return Job(**data)

    ################################################################################

    def __init__(self) -> None:
        # [response-api]
        # ------------------------------------------------------------------------ #
        self.search = self.Search()
        # ------------------------------------------------------------------------ #
        self.job_details = self.JobDetails()
        # ------------------------------------------------------------------------ #


class TheJobApiResponseData:
    def __init__(self) -> None:
        # ------------------------------------------------------------------------ #
        self.job_api: JobApiResponseData = JobApiResponseData()
        # ------------------------------------------------------------------------ #
