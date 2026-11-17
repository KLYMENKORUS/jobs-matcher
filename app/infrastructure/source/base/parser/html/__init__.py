import typing as t

from curl_cffi.requests import Response

from app.infrastructure.source.scraper.browser import AsyncBrowserClient
from app.infrastructure.source.scraper.curl import AsyncCurlScraperClient
from app.infrastructure.source.scraper.http import SourceScraperRequestClient
from app.shared.utils.logger.decorators import delimit_wrapper
from app.shared.utils.requests.schemas import (
    ScraperRequestParams,
    ScraperResponse,
)


class BaseSourceHtmlScraperClient(SourceScraperRequestClient):
    @delimit_wrapper(
        section="request-session",
        obj="request-client",
        detail="fetch data html",
        is_subdelimit=True,
    )
    async def fetch_data(
        self, *, request_params: ScraperRequestParams, **kwargs: t.Any
    ) -> ScraperResponse:

        async with self._fetch(request_params=request_params, **kwargs) as response:
            return ScraperResponse(text=await response.text())

    @delimit_wrapper(
        section="request-session",
        obj="request-client",
        detail="fetch data browser",
        is_subdelimit=True,
    )
    async def fetch_data_browser(
        self, *, request_params: ScraperRequestParams
    ) -> ScraperResponse:
        async with AsyncBrowserClient(
            url=request_params.url,
            logger=self.logger,
            extra_http_headers=request_params.headers,
        ) as client:
            await client.active_page.wait_for_load_state(state="domcontentloaded")

            return ScraperResponse(text=await client.active_page.content())

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
            logger=self.logger,
        ) as client:
            response: Response = await client.get(request_params=request_params)

            return ScraperResponse(text=response.text)
