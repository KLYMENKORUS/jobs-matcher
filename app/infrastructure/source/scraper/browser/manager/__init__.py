__all__ = ("AsyncBrowserManager",)

import contextlib

from playwright.async_api import Browser, Playwright, async_playwright
from playwright_stealth import Stealth

from ..options import ChromeOptions


class AsyncBrowserManager:
    def __init__(self, *, use_headless_mode: bool) -> None:
        # [browser options]
        # ------------------------------------------------------------------------ #
        self.use_headless_mode: bool = use_headless_mode
        # ------------------------------------------------------------------------ #
        self.stealth: Stealth = Stealth()
        # ------------------------------------------------------------------------ #
        self.playwright: Playwright | None = None
        # ------------------------------------------------------------------------ #
        self.browser: Browser | None = None
        # ------------------------------------------------------------------------ #

        # [utils]
        # ------------------------------------------------------------------------ #
        self._chrome_options: ChromeOptions = ChromeOptions()
        # ------------------------------------------------------------------------ #

    async def start(self) -> Browser:
        try:
            self.playwright = await async_playwright().start()
            browser: Browser = await self.playwright.chromium.launch(
                headless=self.use_headless_mode,
                args=self._chrome_options.get_all_chrome_options(),
            )
        except Exception:  # noqa
            await self.shutdown()
            raise

        self.browser = browser
        return browser

    async def shutdown(self) -> None:
        # ------------------------------------------------------------------------ #
        browser: Browser | None = getattr(self, "browser", None)
        playwright: Playwright | None = getattr(self, "playwright", None)

        self.browser = None
        self.playwright = None
        # ------------------------------------------------------------------------ #

        if browser is not None:
            with contextlib.suppress(Exception):
                if browser.is_connected():
                    await browser.close()

        if playwright is not None:
            with contextlib.suppress(Exception):
                await playwright.stop()
