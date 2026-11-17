__all__ = ("BaseScraperRequestClient",)

import typing as t

import ua_generator
from lxml.html import HtmlElement, HTMLParser, fromstring
from pydantic import BaseModel

from app.shared.utils.logger import Logger
from app.shared.utils.logger.enums import LogLabels


class BaseScraperRequestClient:
    def __init__(self, *, logger: Logger) -> None:
        # ------------------------------------------------------------------------ #
        self.logger: Logger = logger
        # ------------------------------------------------------------------------ #
        self.log_labels: LogLabels = LogLabels.SOURCE_API
        # ------------------------------------------------------------------------ #
        self.proxies: dict[str, str] | None = None
        # ------------------------------------------------------------------------ #

    @staticmethod
    def get_random_user_agent() -> dict[str, str]:
        return {
            "user-agent": ua_generator.generate(
                device="desktop",
                platform=["windows", "macos"],
                browser="chrome",
            ).text.strip()
        }

    @staticmethod
    def get_dom_from_html(*, html: str) -> HtmlElement:
        return fromstring(html=html, parser=HTMLParser())

    def update_headers(
        self, *, headers: dict[str, t.Any] | None
    ) -> dict[str, t.Any]:
        return {**(headers or {}), **self.get_random_user_agent()}

    def prepare_request_params(
        self, *, params: BaseModel, exclude_timeout: bool = False
    ) -> dict[str, t.Any]:
        request_params: dict[str, t.Any] = {
            key: value
            for key, value in params.model_dump(
                exclude={
                    "response_format",
                    "allow_redirects",
                    "timeout" if exclude_timeout else "",
                },
                exclude_none=True,
                by_alias=True,
            ).items()
            if value
        }

        if isinstance(self.proxies, dict):
            request_params.update(
                {
                    "proxy": self.proxies.get("https"),
                }
            )
        return request_params
