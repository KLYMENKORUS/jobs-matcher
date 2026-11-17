__all__ = ("logger", "Logger", "LogLabels", "LogLevel")

import os
import sys
import typing as t
import uuid

from loguru import logger as loguru_logger

if t.TYPE_CHECKING:
    from loguru import Record

from app.shared.settings import settings
from app.shared.utils.logger.enums import LogLabels, LogLevel
from app.shared.utils.logger.formatter import ColoredFormatter


class Logger:
    def __init__(
        self,
        *,
        name: str,
        disable_file_handler: bool = False,
        disable_stream_handler: bool = True,
    ) -> None:
        # ------------------------------------------------------------------------ #
        self._name: str = name
        # ------------------------------------------------------------------------ #
        self._logger_id: str = uuid.uuid4().hex
        # ------------------------------------------------------------------------ #

        # [custom-levels]
        # ------------------------------------------------------------------------ #
        for level_name, level_no in LogLevel.name_to_levels().items():
            try:
                loguru_logger.level(level_name)
            except ValueError:
                loguru_logger.level(level_name, no=level_no)
        # ------------------------------------------------------------------------ #

        # [logger]
        # ------------------------------------------------------------------------ #
        self._logger = loguru_logger.bind(logger_id=self._logger_id).patch(
            self._patch_record
        )
        # ------------------------------------------------------------------------ #

        # [file handler]
        # ------------------------------------------------------------------------ #
        if not disable_file_handler:
            loguru_logger.add(
                sink=self._generate_logs_path(),
                level=LogLevel.DEBUG.value,
                format=ColoredFormatter(),
                filter=self._is_own_record,
                colorize=True,
            )
        # ------------------------------------------------------------------------ #

        # [stream handler]
        # ------------------------------------------------------------------------ #
        if not disable_stream_handler:
            loguru_logger.add(
                sink=sys.stdout,
                level=LogLevel.DEBUG.value,
                format=ColoredFormatter(),
                filter=self._is_own_record,
                colorize=True,
            )
        # ------------------------------------------------------------------------ #

    @property
    def name(self) -> str:
        return self._name

    @staticmethod
    def _generate_logs_path(*, filename: str = "logger") -> str:
        log_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "log_files"
        )
        os.makedirs(log_dir, exist_ok=True)
        return os.path.join(log_dir, f"{filename}.log")

    def _is_own_record(self, record: Record) -> bool:
        return bool(record["extra"].get("logger_id") == self._logger_id)

    @staticmethod
    def _patch_record(record: Record) -> None:
        extra: dict[str, t.Any] = record["extra"]

        extra["levelname"] = record["level"].name[:10].ljust(10)
        extra["mode"] = settings.MODE

        path: list[str] = (
            record["file"].path.split("app")[-1].strip(os.sep).split(os.sep)[-2:]
        )
        extra["pathname"] = (
            os.sep.join(path) if path[-1] == "__init__.py" else path[-1]
        )
        extra["lineno"] = f"(l-{record['line']})"

    def _log(
        self, level: LogLevel, msg: str | None, *args: t.Any, **kwargs: t.Any
    ) -> None:
        self._logger.opt(depth=2).log(level.name, msg or "", *args, **kwargs)

    def debug(self, msg: str | None = None, *args: t.Any, **kwargs: t.Any) -> None:
        self._log(LogLevel.DEBUG, msg, *args, **kwargs)

    def subdelimit(
        self, msg: str | None = None, *args: t.Any, **kwargs: t.Any
    ) -> None:
        self._log(LogLevel.SUBDELIMIT, msg, *args, **kwargs)

    def delimit(self, msg: str | None = None, *args: t.Any, **kwargs: t.Any) -> None:
        self._log(LogLevel.DELIMIT, msg, *args, **kwargs)

    def subinfo(self, msg: str | None = None, *args: t.Any, **kwargs: t.Any) -> None:
        self._log(LogLevel.SUBINFO, msg, *args, **kwargs)

    def info(self, msg: str | None = None, *args: t.Any, **kwargs: t.Any) -> None:
        self._log(LogLevel.INFO, msg, *args, **kwargs)

    def detail(self, msg: str | None = None, *args: t.Any, **kwargs: t.Any) -> None:
        self._log(LogLevel.DETAIL, msg, *args, **kwargs)

    def warning(self, msg: str | None = None, *args: t.Any, **kwargs: t.Any) -> None:
        self._log(LogLevel.WARNING, msg, *args, **kwargs)

    def error(self, msg: str | None = None, *args: t.Any, **kwargs: t.Any) -> None:
        self._log(LogLevel.ERROR, msg, *args, **kwargs)


logger = Logger(name="logger")
