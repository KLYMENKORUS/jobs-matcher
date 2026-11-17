__all__ = ("TelegramApiNotifierClient",)

import contextlib
import typing as t

import aiohttp

from app.shared.utils.logger import Logger, LogLabels
from app.shared.utils.logger.decorators import delimit_wrapper
from app.shared.utils.requests.decorators import retry_on_connection_error

from .._base import BaseApiClient
from .request import TelegramApiRequestSendData


class TelegramApiNotifierClient(BaseApiClient):

    def __init__(self, *, logger: Logger, channel_id: str) -> None:
        super().__init__(
            logger=logger, log_labels=LogLabels.TELEGRAM
        )

        # [request data]
        # ------------------------------------------------------------------------ #
        self.request_data: TelegramApiRequestSendData = \
            TelegramApiRequestSendData(channel_id=channel_id)
        # ------------------------------------------------------------------------ #

    @retry_on_connection_error
    @delimit_wrapper(
        section="request-session", obj="telegram-channel",
        detail="send-message", is_subdelimit=True
    )
    async def send_message(
            self, *,
            text: str,
            disable_notification: bool = False,
            reply_to_message_id: int | None = None,
            reply_markup: dict[str, t.Any] | None = None
    ) -> int | None:
        with contextlib.suppress(aiohttp.ClientResponseError):
            response: dict[str, t.Any] = (
                await self.post(
                    **self.request_data.send_message(
                        text=text,
                        disable_notification=disable_notification,
                        reply_to_message_id=reply_to_message_id,
                        reply_markup=reply_markup,
                    )
                )
            )
            message_id: int | None = response.get("result", {}).get("message_id")
            return message_id

        return None

    @retry_on_connection_error
    @delimit_wrapper(
        section="request-session", obj="telegram-channel",
        detail="send-document", is_subdelimit=True
    )
    async def send_document(
            self, *,
            document: str,
            disable_notification: bool = False,
            caption: str | None = None
    ) -> None:
        with contextlib.suppress(aiohttp.ClientResponseError):
            await self.post(
                **self.request_data.send_document(
                    document=document,
                    disable_notification=disable_notification,
                    caption=caption
                )
            )

    @retry_on_connection_error
    @delimit_wrapper(
        section="request-session", obj="telegram-channel",
        detail="send-photo", is_subdelimit=True
    )
    async def send_photo(
            self, *,
            photo: bytes,
            caption: str,
            disable_notification: bool = False
    ) -> None:
        form_data: aiohttp.FormData = aiohttp.FormData()
        request_data: dict[str, t.Any] = self.request_data.send_photo(
            photo=photo, caption=caption,
            disable_notification=disable_notification
        )

        for field, value in request_data["data"].items():
            form_data.add_field(
                name=field, value=(
                    str(value).lower() if isinstance(value, bool) else value
                )
            )

        with contextlib.suppress(aiohttp.ClientResponseError):
            await self.post(
                url=request_data["url"], data=form_data
            )
