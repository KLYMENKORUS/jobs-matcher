__all__ = (
    "UserCreateSchema",
    "UserSchema"
)

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.domains.user_settings.schemas import UserSettingsSchema


class UserCreateSchema(BaseModel):
    telegram_id: int
    keywords: list[str] = Field(default_factory=list)


class UserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    telegram_id: int
    cv_file: str | None
    created_at: datetime
    settings: UserSettingsSchema | None = None
