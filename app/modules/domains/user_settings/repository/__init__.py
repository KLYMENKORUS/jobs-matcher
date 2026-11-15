__all__ = ("UserSettingsRepository",)

from sqlalchemy import cast, func, select
from sqlalchemy.dialects.postgresql import JSONB

from app.infrastructure.database.crud import BaseCRUD
from app.modules.domains.user_settings.models import UserSettings


class UserSettingsRepository(BaseCRUD[UserSettings]):
    model = UserSettings

    async def get_by_user_id(self, *, user_id: int) -> UserSettings | None:
        query = select(UserSettings).where(UserSettings.user_id == user_id)
        return await self.session.scalar(query)

    async def get_unique_active_keywords(self) -> list[str]:
        """Distinct keywords of all active users (`keywords` is a JSON array)."""
        keywords = (
            select(
                func.jsonb_array_elements_text(
                    cast(UserSettings.keywords, JSONB)
                ).label("keyword")
            )
            .where(UserSettings.is_active.is_(True))
            .subquery()
        )
        query = select(keywords.c.keyword).distinct().order_by(keywords.c.keyword)
        return list((await self.session.scalars(query)).all())
