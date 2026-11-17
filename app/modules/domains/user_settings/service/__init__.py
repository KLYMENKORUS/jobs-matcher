__all__ = ("UserSettingsService",)

import typing as t

from app.infrastructure.database.service import UnitOfWork
from app.modules.domains.user_settings.models import UserSettings
from app.modules.domains.user_settings.schemas import (
    UserSettingsSchema,
    UserSettingsUpdateSchema,
)
from app.modules.domains.users.models import User
from app.shared.utils.exceptions.domains.users import UserNotFoundError


class UserSettingsService:
    def __init__(
        self, *, uow_factory: t.Callable[[], UnitOfWork] = UnitOfWork
    ) -> None:
        # ------------------------------------------------------------------------ #
        self._uow_factory: t.Callable[[], UnitOfWork] = uow_factory
        # ------------------------------------------------------------------------ #

    @staticmethod
    async def _get_settings_or_raise(
        uow: UnitOfWork, *, telegram_id: int
    ) -> UserSettings:
        user: User | None = await uow.users.get_by_telegram_id(
            telegram_id=telegram_id
        )
        if user is None:
            raise UserNotFoundError(telegram_id=telegram_id)
        return user.settings

    # [read]
    ################################################################################
    async def get(self, *, telegram_id: int) -> UserSettingsSchema:
        async with self._uow_factory() as uow:
            settings: UserSettings = await self._get_settings_or_raise(
                uow, telegram_id=telegram_id
            )
            return UserSettingsSchema.model_validate(settings)

    async def get_unique_active_keywords(self) -> list[str]:
        async with self._uow_factory() as uow:
            return await uow.user_settings.get_unique_active_keywords()

    ################################################################################

    # [write]
    ################################################################################
    async def update(
        self, *, telegram_id: int, data: UserSettingsUpdateSchema
    ) -> UserSettingsSchema:
        async with self._uow_factory() as uow:
            settings: UserSettings = await self._get_settings_or_raise(
                uow, telegram_id=telegram_id
            )

            # ------------------------------------------------------------------------ #
            for key, value in data.model_dump(
                exclude_unset=True, exclude_none=True
            ).items():
                setattr(settings, key, value)
            await uow.commit()
            # ------------------------------------------------------------------------ #

            return UserSettingsSchema.model_validate(settings)

    ################################################################################
