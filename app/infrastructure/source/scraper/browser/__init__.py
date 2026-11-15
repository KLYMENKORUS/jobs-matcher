__all__ = ("AsyncBrowserClient",)

import contextlib
import traceback
import types
import typing as t
from urllib.parse import parse_qs, urlparse, urlunparse

from playwright.async_api import Browser, BrowserContext, Page

from app.shared.utils.logger import Logger
from app.shared.utils.logger.decorators import delimit_wrapper

from ...base.scraper.browser import AsyncBaseContextClient
from .manager import AsyncBrowserManager
from .options import BrowserContextOptions


class AsyncBrowserClient(AsyncBaseContextClient):
    _WAIT_TIMEOUT: t.Final[float] = 15 * 1000

    def __init__(
            self, *,
            url: str,
            logger: Logger,
            extra_http_headers: dict[str, t.Any],
            proxy_server: str | None = None,
            use_headless_mode: bool = True
    ) -> None:
        super().__init__(logger=logger, proxy_server=proxy_server)

        # ------------------------------------------------------------------------ #
        self.url: str = url
        # ------------------------------------------------------------------------ #
        self.extra_http_headers: dict[str, t.Any] = extra_http_headers
        # ------------------------------------------------------------------------ #

        # [browser options]
        # ------------------------------------------------------------------------ #
        self._browser_manager: AsyncBrowserManager = \
            AsyncBrowserManager(use_headless_mode=use_headless_mode)
        # ------------------------------------------------------------------------ #
        self._browser_context_options: BrowserContextOptions = \
            BrowserContextOptions()
        # ------------------------------------------------------------------------ #

    @delimit_wrapper(
        section="playwright-client", obj="instance-client",
        detail="data extraction", is_subdelimit=True
    )
    async def __aenter__(self) -> AsyncBrowserClient:
        self.logger.info(f"[{self.log_labels}] open connection for playwright client...")

        # ------------------------------------------------------------------------ #
        def _extract_query_params() -> dict[str, t.Any]:
            return {
                param_key: ",".join(param_value[0].split(",") if param_value else param_value)
                for param_key, param_value in parse_qs(urlparse(self.url).query).items()
            }
        # ------------------------------------------------------------------------ #

        try:
            await self.launch_browser_session()
            await self.active_page.goto(url=self.url, timeout=self._WAIT_TIMEOUT)

            self.logger.debug(
                f"[{self.log_labels}] open tab with size: ({await self.get_viewport_size})\n"
                f"request-url: {urlunparse(urlparse(self.url)._replace(query=''))}\n"
                f"params: {_extract_query_params()}"
            )

            return self
        except Exception:  # noqa
            await self.shutdown_browser_session()
            raise

    async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: types.TracebackType | None
    ) -> None:
        await self.shutdown_browser_session()

        if exc_type:
            self.logger.error(f"[{self.log_labels}] {traceback.format_exc(limit=0)}")
            return

        self.logger.info(f"[{self.log_labels}] ...close connection for playwright client")
        return

    async def launch_browser_session(self) -> None:
        # ------------------------------------------------------------------------ #
        browser: Browser = await self._browser_manager.start()

        context: BrowserContext = (
            await browser.new_context(
                proxy=await self.get_proxy_settings(),
                **self._browser_context_options.model_dump(
                    exclude={"extra_http_headers"}
                ),
                extra_http_headers={
                    **self.extra_http_headers,
                    **self._browser_context_options.extra_http_headers
                }
            )
        )
        await self._browser_manager.stealth.apply_stealth_async(
            page_or_context=context
        )
        # ------------------------------------------------------------------------ #

        # ------------------------------------------------------------------------ #
        self.browser = browser
        self.context = context
        self.page = await context.new_page()
        # ------------------------------------------------------------------------ #

        self.logger.debug(
            f"[{self.log_labels}] currently usage User-Agent: "
            f"({self._browser_context_options.user_agent})"
        )

    async def shutdown_browser_session(self) -> None:
        self.logger.debug(f"[{self.log_labels}] closing browser session")

        # ------------------------------------------------------------------------ #
        page: Page | None = self.page
        context: BrowserContext | None = self.context

        self.page = None
        self.context = None
        self.browser = None
        # ------------------------------------------------------------------------ #

        if page is not None:
            with contextlib.suppress(Exception):
                if not page.is_closed():
                    await page.close()

        if context is not None:
            with contextlib.suppress(Exception):
                await context.close()

        await self._browser_manager.shutdown()
