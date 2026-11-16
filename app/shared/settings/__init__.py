__all__ = ("settings",)

from pathlib import Path

from pydantic import Field
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
    ################################################################################

    # [ai-tools]
    ################################################################################
    AI_API_KEY: str
    AI_MODEL_NAME: str
    ################################################################################

    # [telegram]
    ################################################################################
    TELEGRAM_BOT_TOKEN: str

    # task notification channels; an unset channel disables that task's messages
    TELEGRAM_CHANNEL_PARSING: str | None = Field(default=None)
    TELEGRAM_CHANNEL_ANALYSIS: str | None = Field(default=None)
    TELEGRAM_CHANNEL_SENDING: str | None = Field(default=None)
    ################################################################################

    # [matching]
    ################################################################################
    DEFAULT_MIN_SCORE: float = Field(default=70.0, ge=0, le=100)
    ################################################################################

    # [storage]
    ################################################################################
    # uploaded CV files; the bot and the workers must share this directory
    CV_STORAGE_DIR: Path = Field(default=Path("media/cvs"))
    ################################################################################

    # [background tasks]
    ################################################################################
    PARSING_LOOKBACK_DAYS: int = Field(default=30, ge=1)
    ANALYSIS_BATCH_SIZE: int = Field(default=20, ge=1)
    PARSING_INTERVAL_HOURS: int = Field(default=3, ge=1)
    ################################################################################

    @property
    def BROKER_URL(self) -> str:  # noqa: N802 - settings are upper-case
        return (
            f"amqp://{self.RABBITMQ_USERNAME}:{self.RABBITMQ_PASSWORD}"
            f"@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}//"
        )

    @property
    def DATABASE_URL(self) -> str:  # noqa: N802 - settings are upper-case
        return (
            f"postgresql+asyncpg://{self.POSTGRESQL_USER}:{self.POSTGRESQL_PASSWORD}"
            f"@{self.POSTGRESQL_HOST}:{self.POSTGRESQL_PORT}/{self.POSTGRESQL_DB}"
        )


settings = Settings()  # type: ignore[call-arg]
