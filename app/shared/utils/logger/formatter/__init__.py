__all__ = ("ColoredFormatter",)

import typing as t

from termcolor import colored

from app.shared.utils.logger.enums import LogLevel, Style, TextColor

if t.TYPE_CHECKING:
    from loguru import Record


class ColoredFormatter:
    ################################################################################
    class _LogFormat:
        DELIMITER: str = " | "
        FORMAT: t.Final[str] = DELIMITER.join(
            [
                "[{levelname}][{asctime}][{mode}]",
                "{message}",
                "{pathname}/{lineno}",
            ]
        ).strip()

        CELERY_FORMAT: t.Final[str] = DELIMITER.join(
            [
                "[%(levelname)-8s][%(asctime)s][%(processName)s/%(thread)d]",
                "%(message)s",
                "%(pathname)-s/(l-%(lineno)-s)",
            ]
        ).strip()
        DATE_FORMAT: t.Final[str] = "%d.%m.%y/%H:%M:%S"

        LOGURU_FORMAT: t.Final[str] = "{extra[_formatted]}\n{exception}"

    ################################################################################

    def __call__(self, record: Record) -> str:
        # ------------------------------------------------------------------------ #
        record["extra"]["_formatted"] = self.format(record=record)
        # ------------------------------------------------------------------------ #
        return self._LogFormat.LOGURU_FORMAT

    @staticmethod
    def _level_formats(*, msg: str) -> dict[int, tuple[str, ...]]:
        return {
            # DEBUG
            # ------------------------------------------------------------------------ #
            LogLevel.DEBUG: (
                colored(text=msg, color=(color := TextColor.GREY)),
                color,
                TextColor.light_color(color=color),
            ),
            # ------------------------------------------------------------------------ #
            # SUBDELIMIT
            # ------------------------------------------------------------------------ #
            LogLevel.SUBDELIMIT: (
                colored(
                    text=msg,
                    color=(color := TextColor.MAGENTA),
                    on_color=TextColor.on_color(color=color),
                ),
                color,
                TextColor.light_color(color=color),
            ),
            # ------------------------------------------------------------------------ #
            # DELIMIT
            # ------------------------------------------------------------------------ #
            LogLevel.DELIMIT: (
                colored(
                    text=msg,
                    color=(color := TextColor.GREY),
                    on_color=TextColor.on_color(color=color, light="light"),
                ),
                color,
                TextColor.light_color(color=color),
            ),
            # ------------------------------------------------------------------------ #
            # SUBINFO
            # ------------------------------------------------------------------------ #
            LogLevel.SUBINFO: (
                colored(
                    text=msg,
                    color=(color := TextColor.GREEN),
                    attrs=[Style.UNDERLINE],
                ),
                color,
                TextColor.light_color(color=color),
            ),
            # ------------------------------------------------------------------------ #
            # INFO
            # ------------------------------------------------------------------------ #
            LogLevel.INFO: (
                colored(text=msg, color=(color := TextColor.GREEN)),
                color,
                TextColor.light_color(color=color),
            ),
            # ------------------------------------------------------------------------ #
            # WARNING
            # ------------------------------------------------------------------------ #
            LogLevel.WARNING: (
                colored(text=msg, color=(color := TextColor.YELLOW)),
                color,
                TextColor.light_color(color=color),
            ),
            # ------------------------------------------------------------------------ #
            # DETAIL
            # ------------------------------------------------------------------------ #
            LogLevel.DETAIL: (
                colored(text=msg, color=(color := TextColor.CYAN)),
                color,
                TextColor.light_color(color=color),
            ),
            # ------------------------------------------------------------------------ #
            # ERROR
            # ------------------------------------------------------------------------ #
            LogLevel.ERROR: (
                colored(text=msg, color=(color := TextColor.RED)),
                color,
                TextColor.light_color(color=color),
            ),
            # ------------------------------------------------------------------------ #
        }

    def format(self, record: Record) -> str:
        level_formats = self._level_formats(msg=record["message"])
        msg, color, light_color = level_formats.get(
            record["level"].no, level_formats[LogLevel.DEBUG]
        )
        extra: dict[str, t.Any] = record["extra"]

        # ------------------------------------------------------------------------ #
        return self._LogFormat.FORMAT.format(
            message=msg,
            levelname=colored(
                text=extra["levelname"], color=light_color, attrs=[Style.BOLD]
            ),
            mode=colored(text=extra["mode"], color=color, attrs=[Style.DARK]),
            asctime=colored(
                text=record["time"].strftime(self._LogFormat.DATE_FORMAT),
                color=TextColor.light_color(color=TextColor.CYAN),
                attrs=[Style.BOLD, Style.DARK],
            ),
            pathname=colored(
                text=extra["pathname"],
                color=TextColor.light_color(color=TextColor.GREY),
                attrs=[Style.DARK],
            ),
            lineno=colored(
                text=extra["lineno"],
                color=TextColor.light_color(color=TextColor.GREY),
                attrs=[Style.DARK],
            ),
        )
        # ------------------------------------------------------------------------ #

    @classmethod
    def celery_format(cls) -> str:
        return cls._LogFormat.CELERY_FORMAT

    @staticmethod
    def highlight(
        message: str | None,
        sign: str = " ",
        width: int = 75,
        is_upper: bool = True,
    ) -> str:
        text: str = (f" {message} " if message is not None else "").center(
            width, sign
        )
        return text.upper() if is_upper else text
