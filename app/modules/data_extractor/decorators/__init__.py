__all__ = ("data_extractor_validation",)

import functools
import traceback
import typing as t

from aiohttp import ClientResponseError
from curl_cffi.requests.exceptions import HTTPError

from app.shared.utils.exceptions.source import (
    NotAVacancyUrlError,
    SourceApiDataError,
    SourceDataExtractionError,
)
from app.shared.utils.logger import Logger
from app.shared.utils.logger.enums import LogLabels

_PASSTHROUGH_EXCEPTIONS: tuple[type[BaseException], ...] = (
    ClientResponseError,
    HTTPError,
    SourceApiDataError,
    NotAVacancyUrlError,
)


class _DataExtractorValidation:
    """
    Wrap an extractor's `__call__`: anything unexpected becomes
    `SourceDataExtractionError(source, datatype)`, logged with its traceback.

    The wrapped object must expose `logger`, `log_labels` and `source`.
    """

    def __init__(self, *, datatype: str) -> None:
        # ------------------------------------------------------------------------ #
        self._datatype: str = datatype
        # ------------------------------------------------------------------------ #

    def __call__[**P, R](
        self, function: t.Callable[P, t.Coroutine[t.Any, t.Any, R]]
    ) -> t.Callable[P, t.Coroutine[t.Any, t.Any, R]]:

        @functools.wraps(function)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            obj: t.Any = args[0]
            logger: Logger = obj.logger
            log_labels: LogLabels = obj.log_labels

            try:
                return await function(*args, **kwargs)
            except _PASSTHROUGH_EXCEPTIONS:
                raise
            except Exception as exp:
                source: str = str(obj.source)
                logger.error(
                    f"[{log_labels}] {source} data extraction error ({self._datatype} extraction)"
                )
                logger.error(f"[{log_labels}] {traceback.format_exc()}")
                raise SourceDataExtractionError(
                    source=source, datatype=self._datatype
                ) from exp

        return wrapper


data_extractor_validation = _DataExtractorValidation
