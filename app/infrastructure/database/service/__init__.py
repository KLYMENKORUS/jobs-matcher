__all__ = ("UnitOfWork",)

import types
import typing as t

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.infrastructure.database.client import db_client

if t.TYPE_CHECKING:
    from app.modules.domains.user_settings.repository import UserSettingsRepository
    from app.modules.domains.users.repository import UserRepository
    from app.modules.domains.vacancies.repository import (
        InteractionRepository,
        VacancyRepository,
    )


class UnitOfWork:

    ################################################################################
    users: UserRepository
    user_settings: UserSettingsRepository
    vacancies: VacancyRepository
    interactions: InteractionRepository
    ################################################################################

    def __init__(
            self,
            *,
            session_maker: async_sessionmaker[AsyncSession] | None = None
    ) -> None:
        # ------------------------------------------------------------------------ #
        self._session_maker: async_sessionmaker[AsyncSession] = \
            session_maker or db_client.session_maker
        # ------------------------------------------------------------------------ #
        self._session: AsyncSession | None = None
        # ------------------------------------------------------------------------ #

    async def __aenter__(self) -> t.Self:
        from app.modules.domains.user_settings.repository import UserSettingsRepository
        from app.modules.domains.users.repository import UserRepository
        from app.modules.domains.vacancies.repository import (
            InteractionRepository,
            VacancyRepository,
        )

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
        # ------------------------------------------------------------------------ #

        return self

    async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            traceback: types.TracebackType | None
    ) -> None:
        # ------------------------------------------------------------------------ #
        try:
            if exc_type is not None:
                await self.rollback()
        finally:
            await self.session.close()
            self._session = None
        # ------------------------------------------------------------------------ #

    @property
    def session(self) -> AsyncSession:
        if self._session is None:
            raise RuntimeError("UnitOfWork is not started, use `async with UnitOfWork()`")
        return self._session

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()

    async def flush(self) -> None:
        await self.session.flush()
