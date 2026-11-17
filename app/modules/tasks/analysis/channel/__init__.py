__all__ = ("AnalysisTelegramChannel",)

import typing as t

from app.shared.settings import settings
from app.shared.utils.logger import Logger

from ..._base.channels import BaseTelegramChannel


class AnalysisTelegramChannel(BaseTelegramChannel):
    title = "vacancies analysis"

    def __init__(self, *, logger: Logger) -> None:
        super().__init__(
            logger=logger,
            channel_id=settings.TELEGRAM_CHANNEL_ANALYSIS
        )

    @property
    def task_emoji(self) -> str:
        return self.templates.emoji.analysis

    def build_summary(self, *, details: dict[str, t.Any]) -> dict[str, t.Any]:
        return {
            "cvs": len(details.get("cvs") or {}),
            "prefilter rejected": details.get("prefilter_rejected"),
            "analyzed": details.get("analyzed"),
            "duplicates": details.get("duplicates"),
            "failed": details.get("failed"),
        }
