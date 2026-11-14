__all__ = (
    "BaseScraperRequestClient",
    "SourceScraperRequestClient",
)

import contextlib
import traceback
import typing as t

from aiohttp import ClientResponse, ClientResponseError, ClientTimeout

from app.shared.utils.logger import Logger
from app.shared.utils.requests.schemas import ScraperRequestParams
from app.shared.utils.requests.session import AsyncSessionPool

from ...base.scraper.http import BaseScraperRequestClient


class SourceScraperRequestClient(BaseScraperRequestClient):

    def __init__(self, *, logger: Logger) -> None:
        super().__init__(logger=logger)

        # ------------------------------------------------------------------------ #
        self.session_pool: AsyncSessionPool = \
            AsyncSessionPool(logger=self.logger, log_labels=self.log_labels)
        # ------------------------------------------------------------------------ #
        self._timeout: ClientTimeout = ClientTimeout(total=10)
        # ------------------------------------------------------------------------ #

    async def fetch_data(
            self, *, request_params: ScraperRequestParams, **kwargs: t.Any
    ) -> t.Any:
        raise NotImplementedError()

    @contextlib.asynccontextmanager
    async def _fetch(
            self, *, request_params: ScraperRequestParams, **kwargs: t.Any
    ) -> t.AsyncGenerator[ClientResponse]:
        # ------------------------------------------------------------------------ #
        request_params.headers = self.update_headers(headers=request_params.headers)
        params: dict[str, t.Any] = self.prepare_request_params(params=request_params)

        self.logger.debug(
            f"[{self.log_labels}] request client / "
            f"fetch {request_params.method} data / format {request_params.response_format} / "
            f"{request_params.url=}\n"
            f"params = {' '.join(str(params).split())}"
        )
        # ------------------------------------------------------------------------ #

        async with (
            self.session_pool.acquire() as session,
            session.request(**params, **kwargs) as response,
        ):
            try:
                response.raise_for_status()

                self.logger.debug(
                    f"[{self.log_labels}] response status code: {response.status}"
                )
                self.logger.debug(
                    f"[{self.log_labels}] response headers: {dict(response.headers)}"
                )

                yield response

            except ClientResponseError as exp:
                self.logger.error(
                    f"[{self.log_labels}] fetch request error: {traceback.format_exc()}"
                )
                raise exp

            finally:
                if not response.content.at_eof():
                    await response.release()
