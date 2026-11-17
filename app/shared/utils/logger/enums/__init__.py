__all__ = ("LogLevel", "TextColor", "LogLabels", "Style")


import logging
from enum import IntEnum, StrEnum


class LogLevel(IntEnum):
    DEBUG = logging.DEBUG  # 10
    SUBDELIMIT = 11
    DELIMIT = 12
    SUBINFO = 15
    INFO = logging.INFO  # 20
    WARNING = logging.WARNING  # 30
    DETAIL = 35
    ERROR = logging.ERROR  # 40

    @classmethod
    def name_to_levels(cls) -> dict[str, int]:
        return {name: level for name, level in cls.__members__.items()}


class TextColor(StrEnum):
    WHITE = "white"
    GREY = "grey"
    GREEN = "green"
    RED = "red"
    YELLOW = "yellow"
    CYAN = "cyan"
    BLUE = "blue"
    MAGENTA = "magenta"
    BLACK = "black"

    @classmethod
    def on_color(cls, *, color: TextColor, light: str = "") -> str:
        return f"on_{color}" if not light else f"on_{light}_{color}"

    @classmethod
    def light_color(cls, *, color: TextColor) -> str:
        return f"light_{color}"


class Style(StrEnum):
    BOLD = "bold"
    UNDERLINE = "underline"
    DARK = "dark"


class LogLabels(StrEnum):
    # [systems]
    # ------------------------------------------------------------------------ #
    LOGGER = "logger"
    CELERY = "celery"
    DB = "db"
    TELEGRAM = "telegram"
    # ------------------------------------------------------------------------ #

    # [data-extractor]
    # ------------------------------------------------------------------------ #
    SOURCE_API = "source-api"
    DATA_EXTRACTOR = "data-extractor"
    BROWSER_CLIENT = "browser-client"
    # ------------------------------------------------------------------------ #

    # [domains]
    # ------------------------------------------------------------------------ #
    USERS = "users"
    USER_SETTINGS = "user-settings"
    VACANCIES = "vacancies"
    # ------------------------------------------------------------------------ #

    # [tasks]
    # ------------------------------------------------------------------------ #
    PARSING_TASK = "parsing-task"
    ANALYSIS_TASK = "analysis-task"
    SENDING_TASK = "sending-task"
    # ------------------------------------------------------------------------ #
