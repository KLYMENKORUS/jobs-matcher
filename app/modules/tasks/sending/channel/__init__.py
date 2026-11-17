__all__ = ("SendingTelegramChannel",)

import typing as t

from app.shared.settings import settings
from app.shared.utils.logger import Logger

from ..._base.channels import BaseTelegramChannel


class SendingTelegramChannel(BaseTelegramChannel):
    title = "matches sending"
    # runs after every analysis: only a failed run is worth a message
    notify_progress = False

    def __init__(self, *, logger: Logger) -> None:
        super().__init__(
            logger=logger,
            channel_id=settings.TELEGRAM_CHANNEL_SENDING
        )

    @property
    def task_emoji(self) -> str:
        return self.templates.emoji.sending

    def build_summary(self, *, details: dict[str, t.Any]) -> dict[str, t.Any]:
        return {
            "sent": details.get("sent"),
            "not delivered": details.get("failed"),
        }
