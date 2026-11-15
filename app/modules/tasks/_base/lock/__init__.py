__all__ = ("TaskAdvisoryLock",)

import types
import typing as t
import zlib

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from app.infrastructure.database.client import db_client
from app.shared.utils.enums.tasks import TaskType


class TaskAdvisoryLock:
    """
    Postgres session-level advisory lock: one running instance per task type.

    The lock lives on its own connection for the whole run and Postgres drops it
    when that connection closes, so a killed worker never leaves a stale lock
    behind (unlike an `is_running` flag in a table).

        async with TaskAdvisoryLock(task_type=TaskType.PARSING) as acquired:
            if not acquired:
                return  # another worker is running this task
    """

    def __init__(self, *, task_type: TaskType, engine: AsyncEngine | None = None) -> None:
        # ------------------------------------------------------------------------ #
        self._engine: AsyncEngine = engine or db_client.engine
        # ------------------------------------------------------------------------ #
        self._key: int = zlib.crc32(f"jobs-matcher:task:{task_type}".encode())
        # ------------------------------------------------------------------------ #
        self._connection: AsyncConnection | None = None
        # ------------------------------------------------------------------------ #
        self._acquired: bool = False
        # ------------------------------------------------------------------------ #

    async def __aenter__(self) -> bool:
        self._connection = await self._engine.connect()
        self._acquired = bool(
            await self._connection.scalar(select(func.pg_try_advisory_lock(self._key)))
        )
        # end the implicit transaction, the session-level lock stays held
        await self._connection.commit()

        if not self._acquired:
            await self._close()

        return self._acquired

    async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            traceback: types.TracebackType | None
    ) -> None:
        if self._connection is None:
            return

        try:
            if self._acquired:
                await self._connection.scalar(select(func.pg_advisory_unlock(self._key)))
                await self._connection.commit()
        finally:
            await self._close()

    async def _close(self) -> None:
        connection: t.Final = self._connection
        self._connection = None
        if connection is not None:
            await connection.close()
