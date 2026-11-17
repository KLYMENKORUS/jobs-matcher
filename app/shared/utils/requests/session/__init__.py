__all__ = ("AsyncSessionPool",)

import asyncio
import types
from contextlib import AbstractAsyncContextManager

from aiohttp import ClientConnectionError, ClientResponseError, ClientSession

from app.shared.utils.logger import Logger


class AsyncSessionPool:
    ################################################################################
    class _AcquireSessionContextManager(AbstractAsyncContextManager[ClientSession]):
        def __init__(self, *, pool: AsyncSessionPool) -> None:
            # ------------------------------------------------------------------------ #
            self._pool = pool
            # ------------------------------------------------------------------------ #
            self._discard: bool = False
            # ------------------------------------------------------------------------ #
            self._exceptions: tuple[type[Exception], ...] = (
                ClientConnectionError,
                ClientResponseError,
            )
            # ------------------------------------------------------------------------ #

        async def __aenter__(self) -> ClientSession:

            await self._pool._init_pool()
            self._session: ClientSession = await self._pool._acquire_session()
            return self._session

        async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: types.TracebackType | None,
        ) -> None:
            if exc_type and issubclass(exc_type, self._exceptions):
                self._discard = True
                await self._pool._discard_invalid_session(
                    session=self._session, discard=self._discard
                )
                return
            return await self._pool._return_valid_session(session=self._session)

    ################################################################################

    def __init__(self, *, logger: Logger, log_labels: str, size: int = 1) -> None:
        # ------------------------------------------------------------------------ #
        self.log_labels: str = log_labels
        # ------------------------------------------------------------------------ #
        self.logger: Logger = logger
        # ------------------------------------------------------------------------ #
        self._size: int = size
        # ------------------------------------------------------------------------ #
        self._queue: asyncio.Queue[ClientSession] | None = None
        # ------------------------------------------------------------------------ #

    @property
    def queue(self) -> asyncio.Queue[ClientSession]:
        if self._queue is None:
            self._queue = asyncio.Queue(maxsize=self._size)
        return self._queue

    def acquire(self) -> _AcquireSessionContextManager:
        return self._AcquireSessionContextManager(pool=self)

    async def _create_session(self) -> ClientSession:
        self.logger.detail(f"[{self.log_labels}] create request-session...")
        return ClientSession()

    async def _acquire_session(self) -> ClientSession:
        return await self.queue.get()

    async def _init_pool(self) -> None:
        if self.queue.empty():
            self.logger.detail(f"[{self.log_labels}] init session pool...")
            for _ in range(self._size):
                session: ClientSession = await self._create_session()
                await self.queue.put(session)
            return
        self.logger.detail(f"[{self.log_labels}] session pool is full...")

    async def _close_session(self) -> None:
        self.logger.detail(f"[{self.log_labels}] closing session...")
        while not self.queue.empty():
            if not (session := await self.queue.get()).closed:
                await session.close()

    async def _return_valid_session(self, *, session: ClientSession) -> None:
        self.logger.detail(f"[{self.log_labels}] returning valid session to pool")
        await self.queue.put(session)
        await self._close_session()

    async def _discard_invalid_session(
        self, *, session: ClientSession, discard: bool = False
    ) -> None:
        self.logger.info(
            f"[{self.log_labels}] start discard invalid session... ({discard=}, {session.closed=})"
        )
        if discard or session.closed:
            self.logger.warning(
                f"[{self.log_labels}] discarding session ({session.closed=})"
            )
            if not session.closed:
                await session.close()
                self.logger.warning(
                    f"[{self.log_labels}] invalid session successfully closed"
                )
            return
