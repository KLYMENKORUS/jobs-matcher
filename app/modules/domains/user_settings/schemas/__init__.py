__all__ = (
    "UserSettingsSchema",
    "UserSettingsUpdateSchema"
)

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserSettingsSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    keywords: list[str] = Field(default_factory=list)
    is_active: bool = True


class UserSettingsUpdateSchema(BaseModel):
    keywords: list[str] | None = None
    is_active: bool | None = None

    @field_validator("keywords", mode="after")
    @classmethod
    def normalize_keywords(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value

        return list(dict.fromkeys(
            keyword.strip().lower() for keyword in value if keyword.strip()
        ))
