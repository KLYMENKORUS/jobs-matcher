__all__ = ("UnitOfWork",)

import types
import typing as t

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.infrastructure.database.client import db_client

if t.TYPE_CHECKING:
    from app.modules.domains.interactions.repository import (
        InteractionRepository,
    )
    from app.modules.domains.tasks.execution.repository import (
        TaskRunRepository,
    )
    from app.modules.domains.user_settings.repository import (
        UserSettingsRepository,
    )
    from app.modules.domains.users.repository import UserRepository
    from app.modules.domains.vacancies.repository import VacancyRepository


class UnitOfWork:
    """
    Re-entrant: entering an already started UnitOfWork reuses its session and
    only the outermost `async with` closes it. That lets a long-running task open
    one UnitOfWork and hand it to services (`uow_factory=lambda: uow`), whose own
    `async with self._uow_factory()` blocks then share that session.
    An exception inside any level rolls the session back.
    """

    ################################################################################
    users: UserRepository
    user_settings: UserSettingsRepository
    vacancies: VacancyRepository
    interactions: InteractionRepository
    task_runs: TaskRunRepository
    ################################################################################

    def __init__(
        self, *, session_maker: async_sessionmaker[AsyncSession] | None = None
    ) -> None:
        # ------------------------------------------------------------------------ #
        self._session_maker: async_sessionmaker[AsyncSession] = (
            session_maker or db_client.session_maker
        )
        # ------------------------------------------------------------------------ #
        self._session: AsyncSession | None = None
        # ------------------------------------------------------------------------ #
        # how many `async with` blocks are currently inside this UnitOfWork
        self._depth: int = 0
        # ------------------------------------------------------------------------ #

    async def __aenter__(self) -> t.Self:
        self._depth += 1
        if self._session is not None:
            return self

        from app.modules.domains.interactions.repository import (
            InteractionRepository,
        )
        from app.modules.domains.tasks.execution.repository import (
            TaskRunRepository,
        )
        from app.modules.domains.user_settings.repository import (
            UserSettingsRepository,
        )
        from app.modules.domains.users.repository import UserRepository
        from app.modules.domains.vacancies.repository import VacancyRepository

        # [session]
        # ------------------------------------------------------------------------ #
        self._session = self._session_maker()
        # ------------------------------------------------------------------------ #

        # [repositories]
        # ------------------------------------------------------------------------ #
        self.users = UserRepository(session=self._session)
        self.user_settings = UserSettingsRepository(session=self._session)
        self.vacancies = VacancyRepository(session=self._session)
        self.interactions = InteractionRepository(session=self._session)
        self.task_runs = TaskRunRepository(session=self._session)
        # ------------------------------------------------------------------------ #

        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: types.TracebackType | None,
    ) -> None:
        # ------------------------------------------------------------------------ #
        self._depth -= 1
        try:
            if exc_type is not None:
                await self.rollback()
        finally:
            if self._depth == 0:
                await self.session.close()
                self._session = None
        # ------------------------------------------------------------------------ #

    @property
    def session(self) -> AsyncSession:
        if self._session is None:
            raise RuntimeError(
                "UnitOfWork is not started, use `async with UnitOfWork()`"
            )
        return self._session

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()

    async def flush(self) -> None:
        await self.session.flush()
