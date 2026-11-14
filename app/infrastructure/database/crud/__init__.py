__all__ = ("BaseCRUD",)

import typing as t
from collections.abc import Sequence

from sqlalchemy import delete, exists, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.base import Base


class BaseCRUD[ModelT: Base]:
    model: type[ModelT]

    def __init__(self, *, session: AsyncSession) -> None:
        # ------------------------------------------------------------------------ #
        self._session: AsyncSession = session
        # ------------------------------------------------------------------------ #

    @property
    def session(self) -> AsyncSession:
        return self._session

    # [create]
    # ------------------------------------------------------------------------ #
    async def create(self, **values: t.Any) -> ModelT:
        instance: ModelT = self.model(**values)
        self._session.add(instance)
        await self._session.flush()
        return instance

    async def create_many(self, *, items: Sequence[dict[str, t.Any]]) -> list[ModelT]:
        instances: list[ModelT] = [self.model(**values) for values in items]
        self._session.add_all(instances)
        await self._session.flush()
        return instances
    # ------------------------------------------------------------------------ #

    # [read]
    # ------------------------------------------------------------------------ #
    async def get(self, *, id: int) -> ModelT | None:
        return await self._session.get(self.model, id)

    async def get_one_by(self, **filters: t.Any) -> ModelT | None:
        query = select(self.model).filter_by(**filters)
        return await self._session.scalar(query)

    async def get_many(
            self,
            *,
            offset: int = 0,
            limit: int | None = 100,
            **filters: t.Any
    ) -> Sequence[ModelT]:
        query = select(self.model).filter_by(**filters).offset(offset).limit(limit)
        return (await self._session.scalars(query)).all()

    async def exists(self, **filters: t.Any) -> bool:
        query = select(exists().where(
            *(getattr(self.model, key) == value for key, value in filters.items())
        ))
        return bool(await self._session.scalar(query))

    async def count(self, **filters: t.Any) -> int:
        query = select(func.count()).select_from(self.model).filter_by(**filters)
        return int(await self._session.scalar(query) or 0)
    # ------------------------------------------------------------------------ #

    # [update]
    # ------------------------------------------------------------------------ #
    async def update(self, *, id: int, **values: t.Any) -> ModelT | None:
        query = (
            update(self.model)
            .where(self.model.id == id)  # type: ignore[attr-defined]
            .values(**values)
            .returning(self.model)
        )
        return await self._session.scalar(query)
    # ------------------------------------------------------------------------ #

    # [delete]
    # ------------------------------------------------------------------------ #
    async def delete(self, *, id: int) -> bool:
        query = (
            delete(self.model)
            .where(self.model.id == id)  # type: ignore[attr-defined]
            .returning(self.model.id)  # type: ignore[attr-defined]
        )
        return await self._session.scalar(query) is not None
    # ------------------------------------------------------------------------ #
