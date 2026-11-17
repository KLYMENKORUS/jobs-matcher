__all__ = ("BaseTelegramChannel",)

import abc
import datetime as dt
import typing as t
from enum import IntEnum

from app.clients.tg_client import TelegramApiNotifierClient
from app.modules.domains.tasks.execution import TaskRunSchema
from app.shared.settings import settings
from app.shared.utils.logger import Logger

from ...utils.channels.emoji import Emoji
from ...utils.channels.formatter import HtmlFormatter
from ...utils.channels.templates import TemplateRenderer


class BaseTelegramChannel(abc.ABC):
    """
    Telegram channel of one background task: start / end / failed messages of
    its runs. A channel without `channel_id` is disabled and sends nothing.
    """
    title: t.ClassVar[str]
    notify_progress: t.ClassVar[bool] = True

    # telegram rejects messages over 4096 chars, keep the traceback tail
    MAX_EXCEPTION_CHARS: t.Final[int] = 1500

    def __init__(self, *, logger: Logger, channel_id: str | None) -> None:
        # ------------------------------------------------------------------------ #
        self.notifier: TelegramApiNotifierClient | None = (
            TelegramApiNotifierClient(logger=logger, channel_id=channel_id)
            if channel_id else None
        )
        # ------------------------------------------------------------------------ #
        self.templates: TemplateRenderer = TemplateRenderer(
            emoji=Emoji(), formatter=HtmlFormatter()
        )
        # ------------------------------------------------------------------------ #

    @property
    def enabled(self) -> bool:
        return self.notifier is not None

    @property
    @abc.abstractmethod
    def task_emoji(self) -> str:
        pass

    @abc.abstractmethod
    def build_summary(self, *, details: dict[str, t.Any]) -> dict[str, t.Any]:
        pass

    # [messages]
    ################################################################################
    async def send_start_message(
            self, *,
            task_run: TaskRunSchema,
            execution_status: IntEnum,
            celery_details: dict[str, t.Any] | None = None
    ) -> None:
        if not self.notify_progress:
            return

        # ------------------------------------------------------------------------ #
        is_resumed: bool = bool(task_run.timeframes)
        info_message: str = (
            f"{self.task_emoji} {self.title}: "
            f"{'resumed' if is_resumed else 'started'} "
            f"{self.templates.emoji.restart if is_resumed else self.templates.emoji.start}"
        )

        details: dict[str, t.Any] = {
            "run id": task_run.id,
            "started at": self._now().strftime("%d.%m.%Y %H:%M:%S"),
        }

        if is_resumed:
            details["attempt"] = len(task_run.timeframes) + 1
            details["resumed from"] = execution_status.name
        # ------------------------------------------------------------------------ #

        await self._send(
            text=self.templates.render_message(
                info_emoji=self.templates.emoji.info,
                info_message=info_message,
                details=details,
                celery_details=celery_details,
            ),
            disable_notification=True,
        )

    async def send_end_message(
            self, *,
            task_run: TaskRunSchema,
            duration: float,
            celery_details: dict[str, t.Any] | None = None
    ) -> None:
        if not self.notify_progress:
            return

        # ------------------------------------------------------------------------ #
        info_message: str = (
            f"{self.task_emoji} {self.title}: completed {self.templates.emoji.end}"
        )

        details: dict[str, t.Any] = {
            "run id": task_run.id,
            "duration": self._format_duration(duration),
            **{
                key: value
                for key, value in self.build_summary(details=task_run.details).items()
                if value is not None
            },
        }
        # ------------------------------------------------------------------------ #

        await self._send(
            text=self.templates.render_message(
                info_emoji=self.templates.emoji.info,
                info_message=info_message,
                details=details,
                celery_details=celery_details,
            ),
            disable_notification=True,
        )

    async def send_failed_message(
            self, *,
            task_run: TaskRunSchema,
            execution_status: IntEnum,
            exception: str,
            duration: float,
            celery_details: dict[str, t.Any] | None = None
    ) -> None:
        # ------------------------------------------------------------------------ #
        info_message: str = (
            f"{self.templates.emoji.exception}{self.task_emoji} {self.title}: "
            f"failed {self.templates.emoji.cross}"
        )

        details: dict[str, t.Any] = {
            "run id": task_run.id,
            "execution status": execution_status.name,
            "duration": self._format_duration(duration),
            "exception": exception[-self.MAX_EXCEPTION_CHARS:].strip(),
        }
        # ------------------------------------------------------------------------ #

        await self._send(
            text=self.templates.render_message(
                info_emoji=self.templates.emoji.error,
                info_message=info_message,
                details=details,
                warnings=["the run is resumed from this state by the next start"],
                celery_details=celery_details,
            ),
        )
    ################################################################################

    # [helpers]
    ################################################################################
    async def _send(self, *, text: str, disable_notification: bool = False) -> None:
        if self.notifier is None:
            return
        await self.notifier.send_message(
            text=text, disable_notification=disable_notification
        )

    @staticmethod
    def _now() -> dt.datetime:
        return dt.datetime.now(tz=settings.TIME_ZONE)

    @staticmethod
    def _format_duration(seconds: float) -> str:
        minutes, secs = divmod(round(seconds), 60)
        hours, minutes = divmod(minutes, 60)
        return f"{hours}h {minutes:02d}m {secs:02d}s" if hours else f"{minutes}m {secs:02d}s"
    ################################################################################
