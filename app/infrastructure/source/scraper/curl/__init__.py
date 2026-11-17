__all__ = ("AsyncCurlScraperClient",)

import types
import typing as t

from curl_cffi.requests import AsyncSession, Response

from app.shared.utils.requests.schemas import ScraperRequestParams

from ...base.scraper.curl import AsyncBaseCurlScraperClient


class AsyncCurlScraperClient(AsyncBaseCurlScraperClient):
    async def __aenter__(self) -> t.Self:
        self._session = AsyncSession(impersonate="chrome", timeout=10)
        await self._session.__aenter__()  # type: ignore[no-untyped-call]

        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        session: AsyncSession[Response] | None = self._session
        self._session = None

        if session is not None:
            await session.__aexit__(exc_type, exc_val, exc_tb)

    async def get(self, *, request_params: ScraperRequestParams) -> Response:
        request_params.headers = self.update_headers(headers=request_params.headers)
        params: dict[str, t.Any] = self.prepare_request_params(
            params=request_params, exclude_timeout=True
        )

        self.logger.debug(
            f"[{self.log_labels}] request client / "
            f"fetch {request_params.method} data / format {request_params.response_format} / "
            f"{request_params.url=}\n"
            f"params = {' '.join(str(params).split())}"
        )

        response: Response = await self.session.request(**params)
        response.raise_for_status()  # type: ignore[no-untyped-call]

        self.logger.debug(
            f"[{self.log_labels}] response status code: {response.status_code}"
        )
        self.logger.debug(
            f"[{self.log_labels}] response headers: {dict(response.headers)}"
        )

        return response
