__all__ = (
    "UserSettingsSchema",
    "UserSettingsUpdateSchema"
)

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.shared.settings import settings


class UserSettingsSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    keywords: list[str] = Field(default_factory=list)
    is_active: bool = True
    min_score: float = Field(default=settings.DEFAULT_MIN_SCORE, ge=0, le=100)


class UserSettingsUpdateSchema(BaseModel):
    keywords: list[str] | None = None
    is_active: bool | None = None
    min_score: float | None = Field(default=None, ge=0, le=100)

    @field_validator("keywords", mode="after")
    @classmethod
    def normalize_keywords(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value

        return list(dict.fromkeys(
            keyword.strip().lower() for keyword in value if keyword.strip()
        ))
