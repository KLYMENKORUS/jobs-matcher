__all__ = ("TelegramApiRequestSendData",)

import abc
import typing as t
from enum import StrEnum

from app.shared.settings import settings


class TelegramApiRequestSendData:

    ################################################################################
    class Endpoint(StrEnum):
        SEND_MESSAGE = "sendMessage"
        SEND_DOCUMENT = "sendDocument"
        SEND_PHOTO = "sendPhoto"
    ################################################################################

    ################################################################################
    class BaseRequestSendData(abc.ABC):

        def __init__(self, *, parent: TelegramApiRequestSendData) -> None:
            # ------------------------------------------------------------------------ #
            self.parent: TelegramApiRequestSendData = parent
            # ------------------------------------------------------------------------ #

        @abc.abstractmethod
        def get_url(self) -> str:
            pass
    ################################################################################

    ################################################################################
    class SendMessage(BaseRequestSendData):

        def get_url(self) -> str:
            return f"{self.parent.TELEGRAM_API}/{self.parent.Endpoint.SEND_MESSAGE}"

        def __call__(
                self, *,
                text: str,
                disable_notification: bool = False,
                reply_to_message_id: int | None = None
        ) -> dict[str, t.Any]:
            # ------------------------------------------------------------------------ #
            data: dict[str, t.Any] = {
                "chat_id": self.parent.channel_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
                "disable_notification": disable_notification,
            }
            # ------------------------------------------------------------------------ #

            # ------------------------------------------------------------------------ #
            if reply_to_message_id is not None:
                data.update(
                    {
                        "reply_to_message_id": reply_to_message_id,
                        "parse_mode": "MarkdownV2",
                    }
                )
            # ------------------------------------------------------------------------ #

            return {
                "url": self.get_url(),
                "data": data
            }
    ################################################################################

    ################################################################################
    class SendDocument(BaseRequestSendData):

        def get_url(self) -> str:
            return f"{self.parent.TELEGRAM_API}/{self.parent.Endpoint.SEND_DOCUMENT}"

        def __call__(
                self, *,
                document: str,
                disable_notification: bool = False,
                caption: str | None = None
        ) -> dict[str, t.Any]:
            return {
                "url": self.get_url(),
                "data": {
                    "chat_id": self.parent.channel_id,
                    "disable_notification": disable_notification,
                    "parse_mode": "HTML",
                    "caption": caption
                }
            }
    ################################################################################

    ################################################################################
    class SendPhoto(BaseRequestSendData):

        def get_url(self) -> str:
            return f"{self.parent.TELEGRAM_API}/{self.parent.Endpoint.SEND_PHOTO}"

        def __call__(
                self, *,
                photo: bytes,
                caption: str,
                disable_notification: bool = False
        ) -> dict[str, t.Any]:
            return {
                "url": self.get_url(),
                "data": {
                    "chat_id": self.parent.channel_id,
                    "caption": caption,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                    "disable_notification": disable_notification,
                    "photo": photo
                }
            }
    ################################################################################

    def __init__(self, *, channel_id: str) -> None:
        if not settings.TELEGRAM_BOT_TOKEN:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

        # ------------------------------------------------------------------------ #
        self.TELEGRAM_API: t.Final[str] = (
            f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"
        )
        # ------------------------------------------------------------------------ #
        self.channel_id: str = channel_id
        # ------------------------------------------------------------------------ #

        # [request utils]
        # ------------------------------------------------------------------------ #
        self.send_message = self.SendMessage(parent=self)
        # ------------------------------------------------------------------------ #
        self.send_document = self.SendDocument(parent=self)
        # ------------------------------------------------------------------------ #
        self.send_photo = self.SendPhoto(parent=self)
        # ------------------------------------------------------------------------ #
