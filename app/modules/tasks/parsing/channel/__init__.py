__all__ = ("ParsingTelegramChannel",)

import typing as t

from app.shared.settings import settings
from app.shared.utils.logger import Logger

from ..._base.channels import BaseTelegramChannel


class ParsingTelegramChannel(BaseTelegramChannel):
    title = "vacancies parsing"

    def __init__(self, *, logger: Logger) -> None:
        super().__init__(logger=logger, channel_id=settings.TELEGRAM_CHANNEL_PARSING)

    @property
    def task_emoji(self) -> str:
        return self.templates.emoji.parsing

    def build_summary(self, *, details: dict[str, t.Any]) -> dict[str, t.Any]:
        search: dict[str, t.Any] = details.get("search") or {}
        collecting: dict[str, t.Any] = details.get("details") or {}

        return {
            "sources": ", ".join(details.get("sources") or []) or None,
            "keywords": len(details.get("keywords") or []),
            "searches": search.get("searches"),
            "failed searches": search.get("failed"),
            "new vacancies": search.get("new_vacancies"),
            "collected vacancies": collecting.get("collected"),
            "failed vacancies": collecting.get("failed"),
            "linked to users": details.get("linked"),
        }
