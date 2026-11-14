__all__ = ("settings",)

from pydantic import Field, PostgresDsn, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pytz import BaseTzInfo, timezone


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        ignored_types=(BaseTzInfo,),
        extra="allow"
    )

    # [project]
    ################################################################################
    PROJECT_NAME: str
    MODE: str
    TIME_ZONE = timezone("Europe/Kiev")
    ################################################################################

    # [sources]
    ################################################################################
    DOU_URL: str
    DJINNI_URL: str
    THE_JOB_URL: str
    JOBICO_URL: str
    ################################################################################

    # [rabbit celery broker]
    ################################################################################
    RABBITMQ_HOST: str
    RABBITMQ_PORT: int
    RABBITMQ_USERNAME: str
    RABBITMQ_PASSWORD: str
    ################################################################################

    # [postgresql-db]
    ################################################################################
    POSTGRESQL_HOST: str
    POSTGRESQL_PORT: int
    POSTGRESQL_USER: str
    POSTGRESQL_PASSWORD: str
    POSTGRESQL_DB: str
    DATABASE_URL: str | None = Field(default=None)
    ################################################################################

    # [ai-tools]
    ################################################################################
    AI_API_KEY: str
    AI_MODEL_NAME: str
    ################################################################################

    # [telegram]
    ################################################################################
    TELEGRAM_BOT_TOKEN: str
    ################################################################################

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_url(cls, value: str | None, info: ValidationInfo) -> str:
        if value:
            return value

        values = info.data
        url = PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=str(values["POSTGRESQL_USER"]),
            password=str(values["POSTGRESQL_PASSWORD"]),
            host=str(values["POSTGRESQL_HOST"]),
            port=int(values["POSTGRESQL_PORT"]),
            path=str(values["POSTGRESQL_DB"]),
        )
        return str(url)


settings = Settings()  # type: ignore[call-arg]
