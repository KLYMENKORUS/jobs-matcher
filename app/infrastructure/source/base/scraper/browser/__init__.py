__all__ = ("AsyncBaseContextClient",)

import abc
from contextlib import AbstractAsyncContextManager
from urllib.parse import ParseResult, urlparse

from playwright.async_api import Browser, BrowserContext, Page, ProxySettings, ViewportSize

from app.shared.utils.logger import Logger, LogLabels


class AsyncBaseContextClient(
    AbstractAsyncContextManager["AsyncBaseContextClient"], abc.ABC
):

    def __init__(
            self, *, logger: Logger, proxy_server: str | None = None
    ) -> None:
        # ------------------------------------------------------------------------ #
        self.logger: Logger = logger
        # ------------------------------------------------------------------------ #
        self.log_labels: LogLabels = LogLabels.BROWSER_CLIENT
        # ------------------------------------------------------------------------ #
        self.proxy_server: str | None = proxy_server
        # ------------------------------------------------------------------------ #
        self.browser: Browser | None = None
        # ------------------------------------------------------------------------ #
        self.context: BrowserContext | None = None
        # ------------------------------------------------------------------------ #
        self.page: Page | None = None
        # ------------------------------------------------------------------------ #

    @abc.abstractmethod
    async def launch_browser_session(self) -> None:
        pass

    @abc.abstractmethod
    async def shutdown_browser_session(self) -> None:
        pass

    @property
    def active_page(self) -> Page:
        if self.page is None:
            raise RuntimeError("browser session is not launched, call `launch_browser_session()`")
        return self.page

    @property
    async def get_viewport_size(self) -> ViewportSize:
        return ViewportSize(
            width=await self.active_page.evaluate("window.innerWidth"),
            height=await self.active_page.evaluate("window.innerHeight")
        )

    async def get_proxy_settings(self) -> ProxySettings | None:
        if not self.proxy_server:
            return None

        parse_proxy_server: ParseResult = urlparse(url=self.proxy_server)
        protocol, ip, port, username, password = (
            parse_proxy_server.scheme,
            parse_proxy_server.hostname,
            parse_proxy_server.port,
            parse_proxy_server.username,
            parse_proxy_server.password
        )

        proxy_settings: ProxySettings = ProxySettings(
            server=(server := f"{protocol}://{ip}:{port}"),
            username=username, password=password
        )
        self.logger.debug(f"[{self.log_labels}] currently usage proxy: {server}")
        return proxy_settings
