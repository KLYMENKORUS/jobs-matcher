__all__ = ("delimit_wrapper",)

import functools
import inspect
import typing as t

from app.shared.utils.logger import Logger
from app.shared.utils.logger.formatter import ColoredFormatter

type _LoggerDelimit = t.Callable[[str], None]


class _LoggerDelimitWrapper:
    def __init__(
        self,
        *,
        section: str,
        obj: str,
        detail: str,
        is_subdelimit: bool | None = None,
    ) -> None:
        # ------------------------------------------------------------------------ #
        self._section: str = section
        # ------------------------------------------------------------------------ #
        self._obj: str = obj
        # ------------------------------------------------------------------------ #
        self._detail: str = detail
        # ------------------------------------------------------------------------ #
        self._is_subdelimit: bool | None = is_subdelimit
        # ------------------------------------------------------------------------ #

    @property
    def _log(self) -> str:
        return f"[{self._section}] / [{self._obj}] {self._detail}"

    def _get_logger(self, *args: t.Any) -> tuple[Logger, _LoggerDelimit]:
        obj: t.Any = getattr(args[0], "task", args[0])

        logger: Logger = obj.logger
        logger_delimit: _LoggerDelimit = (
            logger.subdelimit if self._is_subdelimit else logger.delimit
        )
        return logger, logger_delimit

    @t.overload
    def __call__[**P, Y](
        self, function: t.Callable[P, t.AsyncIterator[Y]]
    ) -> t.Callable[P, t.AsyncIterator[Y]]: ...

    @t.overload
    def __call__[**P, R](
        self, function: t.Callable[P, t.Coroutine[t.Any, t.Any, R]]
    ) -> t.Callable[P, t.Coroutine[t.Any, t.Any, R]]: ...

    def __call__(self, function: t.Callable[..., t.Any]) -> t.Callable[..., t.Any]:
        # ------------------------------------------------------------------------ #
        if inspect.isasyncgenfunction(function):

            @functools.wraps(function)
            async def gen_wrapper(
                *args: t.Any, **kwargs: t.Any
            ) -> t.AsyncIterator[t.Any]:
                logger, logger_delimit = self._get_logger(*args)
                logger_delimit(ColoredFormatter.highlight(f"start {self._log}"))
                logger.subinfo(f"start {self._log}...")

                try:
                    async for item in function(*args, **kwargs):
                        yield item
                finally:
                    logger.subinfo(f"...end {self._log}")
                    logger_delimit(ColoredFormatter.highlight(f"end {self._log}"))

            return gen_wrapper
        # ------------------------------------------------------------------------ #

        # ------------------------------------------------------------------------ #
        @functools.wraps(function)
        async def wrapper(*args: t.Any, **kwargs: t.Any) -> t.Any:
            logger, logger_delimit = self._get_logger(*args)
            logger_delimit(ColoredFormatter.highlight(f"start {self._log}"))
            logger.subinfo(f"start {self._log}...")

            result: t.Any = await function(*args, **kwargs)

            logger.subinfo(f"...end {self._log}")
            logger_delimit(ColoredFormatter.highlight(f"end {self._log}"))

            return result

        return wrapper
        # ------------------------------------------------------------------------ #


delimit_wrapper = _LoggerDelimitWrapper
