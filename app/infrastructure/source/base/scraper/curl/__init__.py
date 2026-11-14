__all__ = ("AsyncBaseCurlScraperClient",)

import abc
import types
import typing as t

from curl_cffi.requests import AsyncSession, Response

from app.shared.utils.logger import Logger

from ..http import BaseScraperRequestClient


class AsyncBaseCurlScraperClient(BaseScraperRequestClient, abc.ABC):

    def __init__(self, *, logger: Logger, proxies: dict[str, t.Any]) -> None:
        super().__init__(logger=logger)

        # ------------------------------------------------------------------------ #
        self.proxies: dict[str, t.Any] = proxies
        # ------------------------------------------------------------------------ #
        self._session: AsyncSession[Response] | None = None
        # ------------------------------------------------------------------------ #

    @property
    def session(self) -> AsyncSession[Response]:
        if self._session is None:
            raise RuntimeError(
                f"{type(self).__name__} is not started, use `async with {type(self).__name__}()`"
            )
        return self._session

    @abc.abstractmethod
    async def __aenter__(self) -> t.Self:
        pass

    @abc.abstractmethod
    async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: types.TracebackType | None
    ) -> None:
        pass
