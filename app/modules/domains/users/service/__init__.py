__all__ = ("UserService",)

import typing as t

from app.infrastructure.database.service import UnitOfWork
from app.modules.domains.users.models import User
from app.modules.domains.users.schemas import UserCreateSchema, UserSchema
from app.shared.utils.exceptions.domains.users import UserNotFoundError
from app.shared.utils.logger.decorators import delimit_wrapper


class UserService:

    def __init__(self, *, uow_factory: t.Callable[[], UnitOfWork] = UnitOfWork) -> None:
        # ------------------------------------------------------------------------ #
        self._uow_factory: t.Callable[[], UnitOfWork] = uow_factory
        # ------------------------------------------------------------------------ #

    @staticmethod
    async def _get_user_or_raise(uow: UnitOfWork, *, telegram_id: int) -> User:
        user: User | None = await uow.users.get_by_telegram_id(telegram_id=telegram_id)
        if user is None:
            raise UserNotFoundError(telegram_id=telegram_id)
        return user

    # [read]
    ################################################################################
    async def get_by_telegram_id(self, *, telegram_id: int) -> UserSchema | None:
        async with self._uow_factory() as uow:
            user: User | None = await uow.users.get_by_telegram_id(telegram_id=telegram_id)
            return UserSchema.model_validate(user) if user else None

    async def get_active_users(self) -> list[UserSchema]:
        async with self._uow_factory() as uow:
            users = await uow.users.get_active()
            return [UserSchema.model_validate(user) for user in users]
    ################################################################################

    # [write]
    ################################################################################
    @delimit_wrapper(section="users", obj="service", detail="register", is_subdelimit=True)
    async def register(self, *, data: UserCreateSchema) -> UserSchema:
        async with self._uow_factory() as uow:
            # ------------------------------------------------------------------------ #
            user: User | None = await uow.users.get_by_telegram_id(
                telegram_id=data.telegram_id
            )
            if user is not None:
                return UserSchema.model_validate(user)
            # ------------------------------------------------------------------------ #

            # ------------------------------------------------------------------------ #
            user = await uow.users.create_with_settings(
                telegram_id=data.telegram_id, keywords=data.keywords
            )
            await uow.commit()
            # ------------------------------------------------------------------------ #

            return UserSchema.model_validate(user)

    async def update_cv(self, *, telegram_id: int, cv_text: str) -> UserSchema:
        async with self._uow_factory() as uow:
            user: User = await self._get_user_or_raise(uow, telegram_id=telegram_id)
            user.cv_text = cv_text.strip()
            await uow.commit()

            return UserSchema.model_validate(user)

    async def delete(self, *, telegram_id: int) -> None:
        async with self._uow_factory() as uow:
            user: User = await self._get_user_or_raise(uow, telegram_id=telegram_id)
            await uow.session.delete(user)
            await uow.commit()
    ################################################################################
