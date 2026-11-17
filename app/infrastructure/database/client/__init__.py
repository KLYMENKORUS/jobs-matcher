__all__ = ("DatabaseClient", "db_client")

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.shared.settings import settings


class DatabaseClient:
    def __init__(
        self,
        *,
        url: str | None = None,
        echo: bool = False,
        is_null_pool: bool = False,
        pool_size: int = 10,
        max_overflow: int = 20,
    ) -> None:
        # ------------------------------------------------------------------------ #
        self._url: str = url or str(settings.DATABASE_URL)
        # ------------------------------------------------------------------------ #

        # [engine]
        # ------------------------------------------------------------------------ #
        pool_kwargs = (
            {"poolclass": NullPool}
            if is_null_pool
            else {
                "pool_size": pool_size,
                "max_overflow": max_overflow,
                "pool_pre_ping": True,
            }
        )
        self._engine: AsyncEngine = create_async_engine(
            url=self._url,
            echo=echo,
            **pool_kwargs,
        )
        # ------------------------------------------------------------------------ #

        # [session maker]
        # ------------------------------------------------------------------------ #
        self._session_maker: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
        # ------------------------------------------------------------------------ #

    @property
    def engine(self) -> AsyncEngine:
        return self._engine

    @property
    def session_maker(self) -> async_sessionmaker[AsyncSession]:
        return self._session_maker

    def session(self) -> AsyncSession:
        return self._session_maker()

    async def dispose(self) -> None:
        await self._engine.dispose()


db_client = DatabaseClient()
