__all__ = (
    "OrderByDate",
    "TheJobApiRequestData",
)

import typing as t
from enum import StrEnum
from http import HTTPMethod

from app.shared.settings import settings

from .....base.parser.api import BaseSourceApiRequestData

type OrderByDate = t.Literal["asc", "desc"]


class JobApiRequestData(BaseSourceApiRequestData):

    ################################################################################
    class Endpoint(StrEnum):
        JOB = "job"
    ################################################################################

    # [search]
    ################################################################################
    class Search(BaseSourceApiRequestData.BaseSourceEndpointData):
        """`GET /api/job` — paginated job search (20 per page, see `pagination`)."""

        COUNTRY_CODE: t.Final[str] = "6243950719002638747"
        JOB_LOCATION: t.Final[str] = "Remote"
        SALARY_CURRENCY: t.Final[str] = "USD"

        def __init__(self, *, parent: JobApiRequestData) -> None:
            # ------------------------------------------------------------------------ #
            self._parent: JobApiRequestData = parent
            # ------------------------------------------------------------------------ #
            self.http_method: HTTPMethod = HTTPMethod.GET
            # ------------------------------------------------------------------------ #

        def get_url(self) -> str:
            return f"{self._parent.url}/{self._parent.Endpoint.JOB}"

        def _build_params(
                self, *,
                query: str,
                page: int,
                order_by_date: OrderByDate | None,
        ) -> dict[str, t.Any]:
            return self.prepare_params(
                **{
                    "query": query.strip(),
                    "page": page,
                    "jobLocation": self.JOB_LOCATION,
                    "country": self.COUNTRY_CODE,
                    "salaryCurrency": self.SALARY_CURRENCY,
                    "order_by_date": order_by_date,
                }
            )

        def get(
                self, *,
                query: str,
                page: int = 1,
                order_by_date: OrderByDate | None = "desc",
        ) -> dict[str, t.Any]:
            return {
                "url": self.get_url(),
                "method": self.http_method,
                "params": self._build_params(
                    query=query,
                    page=page,
                    order_by_date=order_by_date
                )
            }
    ################################################################################

    # [details]
    ################################################################################
    class JobDetails(BaseSourceApiRequestData.BaseSourceEndpointData):
        """`GET /api/job/{job_slug}` — a single job; accepts the job id or its slug."""

        def __init__(self, *, parent: JobApiRequestData) -> None:
            # ------------------------------------------------------------------------ #
            self._parent: JobApiRequestData = parent
            # ------------------------------------------------------------------------ #
            self.http_method: HTTPMethod = HTTPMethod.GET
            # ------------------------------------------------------------------------ #

        def get_url(self, *, job_slug: str) -> str:
            return f"{self._parent.url}/{self._parent.Endpoint.JOB}/{job_slug}"

        def get(self, *, job_id: str) -> dict[str, t.Any]:
            return {
                "url": self.get_url(job_slug=job_id),
                "method": self.http_method,
            }
    ################################################################################

    def __init__(self) -> None:
        # ------------------------------------------------------------------------ #
        self.url: str = f"{settings.THE_JOB_URL}/api"
        # ------------------------------------------------------------------------ #

        # [request-api]
        # ------------------------------------------------------------------------ #
        self.search = self.Search(parent=self)
        # ------------------------------------------------------------------------ #
        self.job_details = self.JobDetails(parent=self)
        # ------------------------------------------------------------------------ #


class TheJobApiRequestData:

    def __init__(self) -> None:
        # ------------------------------------------------------------------------ #
        self.job_api: JobApiRequestData = JobApiRequestData()
        # ------------------------------------------------------------------------ #
