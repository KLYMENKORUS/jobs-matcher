__all__ = ("UserSettingsRepository",)

from sqlalchemy import select

from app.infrastructure.database.crud import BaseCRUD
from app.modules.domains.user_settings.models import UserSettings


class UserSettingsRepository(BaseCRUD[UserSettings]):
    model = UserSettings

    async def get_by_user_id(self, *, user_id: int) -> UserSettings | None:
        query = select(UserSettings).where(UserSettings.user_id == user_id)
        return await self.session.scalar(query)
