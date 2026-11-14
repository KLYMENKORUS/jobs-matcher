__all__ = (
    "retry_on_connection_error",
)

import asyncio
import random
import typing as t

from aiohttp import ClientConnectionError, ClientResponseError
from curl_cffi.requests.exceptions import HTTPError
from playwright.async_api import Error as PlaywrightError
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from tenacity import (
    AsyncRetrying,
    RetryCallState,
    retry_if_exception,
    stop_after_attempt,
)

from app.shared.utils.descriptors import BaseAttributeAccessor
from app.shared.utils.logger import Logger
from app.shared.utils.logger import logger as default_logger

from ..config import HTTPRetryConfig


class _RetryOnConnectionError[T](BaseAttributeAccessor[T]):
    """
    Retry an async request on connection errors / retryable HTTP statuses.

    Usage:
        @retry_on_connection_error
        async def fetch(self, ...): ...

        @retry_on_connection_error.with_config(HTTPRetryConfig(exp_statuses={...}))
        async def fetch(self, ...): ...

    Pass `retry_on_failure=False` at call time to run a single attempt.
    """

    _RETRY_EXCEPTIONS: t.ClassVar[tuple[type[BaseException], ...]] = (
        ClientConnectionError,
        ClientResponseError,
        HTTPError,
        asyncio.TimeoutError,
        PlaywrightError,
        PlaywrightTimeoutError,
    )

    def __init__(
            self,
            function: t.Callable[..., t.Awaitable[T]],
            *,
            config: HTTPRetryConfig | None = None
    ) -> None:
        super().__init__(function)

        # ------------------------------------------------------------------------ #
        self._retry_config: HTTPRetryConfig = config or HTTPRetryConfig()
        # ------------------------------------------------------------------------ #

    @staticmethod
    def with_config[R](
            config: HTTPRetryConfig,
    ) -> t.Callable[[t.Callable[..., t.Awaitable[R]]], _RetryOnConnectionError[R]]:
        def decorator(function: t.Callable[..., t.Awaitable[R]]) -> _RetryOnConnectionError[R]:
            return _RetryOnConnectionError(function, config=config)
        return decorator

    def __get__(self, instance: t.Any, owner: type[t.Any] | None = None) -> t.Self:
        # same as BaseAttributeAccessor.__get__, but carries the config over
        if instance is None:
            return self
        bound: t.Self = self.__class__(
            self.function.__get__(instance, owner),
            config=self._retry_config,
        )
        bound.instance = instance
        return bound

    # [logging]
    ################################################################################
    @property
    def _logger(self) -> Logger:
        return getattr(self.instance, "logger", default_logger)

    @property
    def _log_labels(self) -> str:
        return str(getattr(self.instance, "log_labels", "request"))
    ################################################################################

    # [tenacity callbacks]
    ################################################################################
    def _should_retry(self, exp: BaseException) -> bool:
        if isinstance(exp, ClientResponseError):
            return exp.status in self._retry_config.get_exp_statuses()

        return isinstance(exp, self._RETRY_EXCEPTIONS)

    def _get_retry_delay(self, retry_state: RetryCallState) -> float:
        # exponential backoff capped at MAX_DELAY, plus jitter proportional to the delay
        attempt: int = retry_state.attempt_number - 1
        delay: float = min(
            self._retry_config.BASE_DELAY * (2 ** attempt) * self._retry_config.FACTOR,
            self._retry_config.MAX_DELAY,
        )
        return delay + random.uniform(0, delay * self._retry_config.JITTER_RATIO)

    def _log_failed_attempt(self, retry_state: RetryCallState) -> None:
        exp: BaseException | None = (
            retry_state.outcome.exception() if retry_state.outcome else None
        )

        self._logger.error(f"[{self._log_labels}] request connection error: {exp!r}")
        self._logger.warning(
            f"[{self._log_labels}] request failed attempt "
            f"{retry_state.attempt_number}/{self._retry_config.CONNECTION_ERR_RETRIES}"
        )
    ################################################################################

    def _build_retrying(self) -> AsyncRetrying:
        return AsyncRetrying(
            stop=stop_after_attempt(self._retry_config.CONNECTION_ERR_RETRIES),
            wait=self._get_retry_delay,
            retry=retry_if_exception(self._should_retry),
            after=self._log_failed_attempt,
            reraise=True,
        )

    async def __call__(self, *args: t.Any, **kwargs: t.Any) -> T:
        if not kwargs.pop("retry_on_failure", True):
            return await self.function(*args, **kwargs)

        result: T = await self._build_retrying()(self.function, *args, **kwargs)
        return result


retry_on_connection_error = _RetryOnConnectionError
