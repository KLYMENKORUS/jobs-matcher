__all__ = ("UserRepository",)

from collections.abc import Sequence

from sqlalchemy import select

from app.infrastructure.database.crud import BaseCRUD
from app.modules.domains.user_settings.models import UserSettings
from app.modules.domains.users.models import User


class UserRepository(BaseCRUD[User]):
    model = User

    async def get_by_telegram_id(self, *, telegram_id: int) -> User | None:
        query = select(User).where(User.telegram_id == telegram_id)
        return await self.session.scalar(query)

    async def create_with_settings(
        self, *, telegram_id: int, keywords: list[str] | None = None
    ) -> User:
        user = User(
            telegram_id=telegram_id,
            settings=UserSettings(keywords=keywords or []),
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def get_active(self) -> Sequence[User]:
        query = (
            select(User)
            .join(User.settings)
            .where(UserSettings.is_active.is_(True), User.cv_file.is_not(None))
            .order_by(User.id)
        )
        return (await self.session.scalars(query)).all()
