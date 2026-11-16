__all__ = ("TemplateRenderer",)

import typing as t
from html import escape

from app.shared.settings import settings

from ..emoji import Emoji
from ..formatter import HtmlFormatter


class TemplateRenderer:
    BLOCK_KEYS: t.Final[tuple[str, ...]] = ("exception",)

    def __init__(self, *, emoji: Emoji, formatter: HtmlFormatter) -> None:
        # ------------------------------------------------------------------------ #
        self.emoji: Emoji = emoji
        # ------------------------------------------------------------------------ #
        self.formatter: HtmlFormatter = formatter
        # ------------------------------------------------------------------------ #

    def render_project_name(self) -> str:
        return f"{self.emoji.project} {self.formatter.bold(text=escape(settings.PROJECT_NAME))}"

    def render_mode(self) -> str:
        return f"{self.emoji.mode} {self.formatter.bold(text=escape(settings.MODE))}"

    def render_info(self, *, info_message: str, info_emoji: str | None) -> str:
        if info_emoji is not None:
            return (
                f"{self.emoji.task}{info_emoji}{self.emoji.speech}:   "
                f"{self.formatter.italic(text=info_message)}"
            )
        return self.formatter.italic(text=info_message)

    def render_details(self, *, details: dict[str, t.Any]) -> str:
        # ------------------------------------------------------------------------ #
        def _render_value(*, key: str, value: t.Any) -> str:
            if "url" in key:
                return self.formatter.link(
                    url=escape(str(value), quote=True), text=escape(str(value))
                )

            if key in self.BLOCK_KEYS:
                return self.formatter.code_block(text=escape(str(value)))

            return self.formatter.code(text=escape(str(value)))
        # ------------------------------------------------------------------------ #

        return "\n".join(
            f"{self.emoji.detail} {self.formatter.bold(text=escape(key))}: "
            f"{_render_value(key=key, value=value)}"
            for key, value in details.items()
        )

    def render_warnings(self, *, warnings: list[str]) -> str:
        return "\n".join(
            f"{self.emoji.warn} {self.formatter.italic(text=escape(warn))}"
            for warn in warnings
        )

    def render_celery_details(self, *, celery_details: dict[str, t.Any]) -> str:
        return "\n".join(
            f"{self.emoji.celery} {self.formatter.bold(text=escape(key))}: "
            f"{self.formatter.spoiler(text=escape(str(value)))}"
            for key, value in celery_details.items()
            if value is not None
        )

    def render_message(
            self, *,
            info_message: str,
            info_emoji: str | None = None,
            details: dict[str, t.Any] | None = None,
            warnings: list[str] | None = None,
            celery_details: dict[str, t.Any] | None = None,
    ) -> str:
        # ------------------------------------------------------------------------ #
        message: str = (
            f"{self.emoji.work} {self.render_project_name()} {self.render_mode()}\n\n"
            f"{self.render_info(info_emoji=info_emoji, info_message=info_message)}"
        )
        # ------------------------------------------------------------------------ #

        # ------------------------------------------------------------------------ #
        if warnings:
            message += f"\n\n{self.render_warnings(warnings=warnings)}"

        if details:
            message += f"\n\n{self.render_details(details=details)}"

        if celery_details:
            message += f"\n\n{self.render_celery_details(celery_details=celery_details)}"
        # ------------------------------------------------------------------------ #

        return message
