__all__ = ("BaseApiClient",)

import typing as t
from http import HTTPStatus

from aiohttp import ClientResponse

from app.shared.utils.logger import Logger
from app.shared.utils.logger.enums import LogLabels
from app.shared.utils.requests.session import AsyncSessionPool


class BaseApiClient:
    def __init__(self, *, logger: Logger, log_labels: LogLabels) -> None:

        # ------------------------------------------------------------------------ #
        self.logger: Logger = logger
        # ------------------------------------------------------------------------ #
        self.log_labels: LogLabels = log_labels
        # ------------------------------------------------------------------------ #
        self.session_pool: AsyncSessionPool = AsyncSessionPool(
            logger=self.logger, log_labels=self.log_labels
        )
        # ------------------------------------------------------------------------ #

    async def post(self, *, url: str, **kwargs: t.Any) -> t.Any:
        async with self.session_pool.acquire() as session:
            response: ClientResponse = await session.post(url, **kwargs)
            response.raise_for_status()

            return (
                await response.json()
                if response.status != HTTPStatus.NO_CONTENT
                else None
            )

    async def get(self, *, url: str, **kwargs: t.Any) -> t.Any:
        async with self.session_pool.acquire() as session:
            response: ClientResponse = await session.get(url, **kwargs)
            response.raise_for_status()
            return await response.json()

    async def put(self, *, url: str, **kwargs: t.Any) -> t.Any:
        async with self.session_pool.acquire() as session:
            response: ClientResponse = await session.put(url, **kwargs)
            response.raise_for_status()
            return await response.json()

    async def delete(self, *, url: str, **kwargs: t.Any) -> None:
        async with self.session_pool.acquire() as session:
            await session.delete(url, **kwargs)
