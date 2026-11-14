__all__ = ("HTTPRetryConfig",)

import typing as t
from http import HTTPStatus


class HTTPRetryConfig:
    CONNECTION_ERR_RETRIES: t.Final[int] = 3

    BASE_DELAY: t.Final[float] = 0.8
    FACTOR: t.Final[float] = 1.0
    MAX_DELAY: t.Final[float] = 12.0
    JITTER_RATIO: t.Final[float] = 0.4

    EXCEPTION_STATUSES: set[HTTPStatus] = {
        HTTPStatus.FORBIDDEN,
        HTTPStatus.INTERNAL_SERVER_ERROR,
        HTTPStatus.NOT_IMPLEMENTED,
        HTTPStatus.BAD_GATEWAY,
        HTTPStatus.SERVICE_UNAVAILABLE,
        HTTPStatus.GATEWAY_TIMEOUT,
        HTTPStatus.PROXY_AUTHENTICATION_REQUIRED
    }

    def __init__(self, *, exp_statuses: set[HTTPStatus] | None = None) -> None:
        # ------------------------------------------------------------------------ #
        self.exp_statuses: set[HTTPStatus] | None = exp_statuses
        # ------------------------------------------------------------------------ #

    def get_exp_statuses(self) -> set[HTTPStatus]:
        return self.exp_statuses or self.EXCEPTION_STATUSES
