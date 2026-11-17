__all__ = ("TheJobParserRequestClient",)

from curl_cffi.requests import Response

from app.infrastructure.source.scraper.curl import AsyncCurlScraperClient
from app.infrastructure.source.scraper.http import SourceScraperRequestClient
from app.shared.utils.logger.decorators import delimit_wrapper
from app.shared.utils.requests.decorators import retry_on_connection_error
from app.shared.utils.requests.schemas import (
    ScraperRequestParams,
    ScraperResponse,
)

from ._request import OrderByDate, TheJobApiRequestData
from ._response import TheJobApiResponseData


class TheJobParserRequestClient(SourceScraperRequestClient):
    """thejob.tech API client"""

    request_data: TheJobApiRequestData = TheJobApiRequestData()
    response_data: TheJobApiResponseData = TheJobApiResponseData()

    @delimit_wrapper(
        section="request-session",
        obj="request-client",
        detail="fetch data curl",
        is_subdelimit=True,
    )
    async def fetch_data_curl(
        self, *, request_params: ScraperRequestParams
    ) -> ScraperResponse:
        async with AsyncCurlScraperClient(
            logger=self.logger, proxies=self.proxies
        ) as client:
            response: Response = await client.get(request_params=request_params)
            return ScraperResponse(json_data=response.json())

    # [job-api]
    ################################################################################
    # /job
    @retry_on_connection_error
    async def search(
        self,
        *,
        query: str,
        page: int = 1,
        order_by_date: OrderByDate | None = "desc",
    ) -> ScraperResponse:
        return await self.fetch_data_curl(
            request_params=ScraperRequestParams(
                **self.request_data.job_api.search.get(
                    query=query, page=page, order_by_date=order_by_date
                )
            )
        )

    # /job/{job_slug}
    @retry_on_connection_error
    async def job_details(self, *, job_id: str) -> ScraperResponse:
        return await self.fetch_data_curl(
            request_params=ScraperRequestParams(
                **self.request_data.job_api.job_details.get(job_id=job_id)
            )
        )

    ################################################################################
