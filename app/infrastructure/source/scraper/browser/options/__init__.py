__all__ = (
    "ChromeOptions",
    "BrowserContextOptions",
)

import typing as t

import ua_generator
from pydantic import BaseModel, Field

from app.shared.settings import settings


class ChromeOptions(BaseModel):
    no_sandbox: str = Field(
        default="--no-sandbox",
        description=(
            "Disables Chrome's sandbox security model."
            "Commonly required in Docker and CI environments."
        )
    )
    disable_blink_features: str = Field(
        default="--disable-blink-features=AutomationControlled",
        description=(
            "Disables the AutomationControlled Blink feature "
            "to reduce automation fingerprinting."
        )
    )
    disable_blink_features_site_per_process: str = Field(
        default="--disable-blink-features=site-per-process",
        description=(
            "Disables Blink's site-per-process isolation feature, "
            "which forces each site into a separate renderer process."
        )
    )
    disable_gpu: str = Field(
        default="--disable-gpu",
        description="Disables GPU hardware acceleration. Can be helpful in environments where "
                    "GPU support is unavailable or unstable."
    )
    disable_dev_shm_usage: str = Field(
        default="--disable-dev-shm-usage",
        description=(
            "Disables shared memory (/dev/shm) usage, directing "
            "Chrome to write shared memory files to disk instead."
        )
    )
    disable_audio_output: str = Field(
        default="--disable-audio-output",
        description="Kills the audio utility process (--type=utility audio.mojom.AudioService)."
    )
    disable_background_networking: str = Field(
        default="--disable-background-networking",
        description="Kills excess network utility processes when creating a new browser context."
    )
    disable_extensions: str = Field(
        default="--disable-extensions",
        description="Prevents Chrome from loading browser extensions."
    )
    disable_infobars: str = Field(
        default="--disable-infobars",
        description="Hides informational banners such as automation notifications."
    )
    disable_breakpad: str = Field(
        default="--disable-breakpad",
        description="Disables Chrome crash reporting through Breakpad."
    )
    disable_component_extensions_with_background_pages: str = Field(
        default="--disable-component-extensions-with-background-pages",
        description=(
            "Disables extensions with background pages, "
            "which can consume resources even when not in use."
        )
    )
    dns_prefetch_disable: str = Field(
        default="--dns-prefetch-disable",
        description=(
            "Disables DNS prefetching to prevent Chrome from making speculative "
            "DNS lookups for links it might not visit."
        )
    )
    ignore_certificate_errors: str = Field(
        default="--ignore-certificate-errors",
        description="Ignores SSL/TLS certificate validation errors."
    )
    ignore_ssl_errors: str = Field(
        default="--ignore-ssl-errors",
        description="Allows connections to websites with invalid SSL certificates."
    )
    allow_running_insecure_content: str = Field(
        default="--allow-running-insecure-content",
        description="Allows loading insecure HTTP resources on HTTPS pages."
    )
    no_first_run: str = Field(
        default="--no-first-run",
        description="Skips Chrome's first-run experience and setup screens."
    )
    no_default_browser_check: str = Field(
        default="--no-default-browser-check",
        description="Disables the default browser check on startup."
    )
    disable_popup_blocking: str = Field(
        default="--disable-popup-blocking",
        description="Disables Chrome's popup blocking mechanism."
    )

    def get_all_chrome_options(self) -> list[str]:
        return list(self.model_dump().values())


class BrowserContextOptions(BaseModel):
    color_scheme: str = Field(
        default="dark",
        description="Color scheme to use for the browser ('light' or 'dark')"
    )
    user_agent: str = Field(
        default_factory=lambda: ua_generator.generate(
            device="desktop",
            platform=["macos"],
            browser="chrome"
        ).text.strip(),
        description="User agent string to use for the browser"
    )
    locale: str = Field(
        default="uk-UA",
        description="Locale to be used in the browser (e.g., 'ua-UA')"
    )
    timezone_id: str = Field(
        default=settings.TIME_ZONE.zone,
        description="Timezone ID for the browser session (e.g., 'Europe/Kyiv')"
    )
    java_script_enabled: bool = Field(
        default=True,
        description=(
            "Enables JavaScript execution in the browser."
            "Disable only for static page rendering or testing scenarios."
        )
    )
    bypass_csp: bool = Field(
        default=False,
        description=(
            "Bypasses Content Security Policy (CSP) restrictions, "
            "allowing script injection and execution on pages with strict CSP rules."
        )
    )
    ignore_https_errors: bool = Field(
        default=True,
        description=(
            "Ignores HTTPS and SSL certificate validation "
            "errors when navigating to websites."
        )
    )
    viewport: dict[str, t.Any] = Field(
        default_factory=lambda: dict(width=1680, height=1050),
        description="Viewport size for the browser window (width and height in pixels)"
    )
    extra_http_headers: dict[str, str] = Field(
        default_factory=lambda: {
            "Accept-Language": "uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7"
        },
        description=(
            "Default HTTP headers used to mimic a modern desktop browser and "
            "provide realistic navigation requests."
        )
    )
