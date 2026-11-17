__all__ = (
    "BaseCeleryApp",
    "BaseTaskWithRetry",
    "run_async_task",
)

import asyncio
import typing as t

from aiohttp import (
    ClientConnectionError,
    ClientConnectorError,
    ClientResponseError,
)
from celery import Celery, Task

from app.infrastructure.database.client import db_client
from app.shared.settings import settings
from app.shared.utils.logger import LogLabels


class BaseCeleryApp(Celery):  # type: ignore[misc]
    def __init__(self, *, main: str, broker: str) -> None:
        super().__init__(main=main, broker=broker)

        # ------------------------------------------------------------------------ #
        self.log_labels: LogLabels = LogLabels.CELERY
        # ------------------------------------------------------------------------ #

        # [broker settings]
        # ------------------------------------------------------------------------ #
        self.conf.update(broker_connection_retry_on_startup=True)
        # ------------------------------------------------------------------------ #

        # [worker settings]
        # ------------------------------------------------------------------------ #
        # one task per child process: every task gets a fresh event loop and a
        # fresh db engine (asyncpg connections can not outlive their loop)
        self.conf.update(worker_max_tasks_per_child=1)
        self.conf.update(worker_prefetch_multiplier=1)
        self.conf.update(worker_hijack_root_logger=False)
        self.conf.update(worker_redirect_stdouts=False)
        # monitoring events (same as `-E`): flower discovers workers only from
        # their heartbeats, a worker without events never shows up in the ui
        self.conf.update(worker_send_task_events=True)
        self.conf.update(task_send_sent_event=True)
        # ------------------------------------------------------------------------ #

        # [task settings]
        # ------------------------------------------------------------------------ #
        # the message is acked only after the task finished, a killed worker
        # gets it redelivered and the task resumes from its saved state
        self.conf.update(task_acks_late=True)
        self.conf.update(task_reject_on_worker_lost=True)
        # ------------------------------------------------------------------------ #

        # [timezone settings]
        # ------------------------------------------------------------------------ #
        self.conf.update(timezone=str(settings.TIME_ZONE))
        self.conf.update(enable_utc=False)
        # ------------------------------------------------------------------------ #


class BaseTaskWithRetry(Task):  # type: ignore[misc]
    abstract: bool = True
    autoretry_for = (
        ClientResponseError,
        ClientConnectionError,
        ClientConnectorError,
    )
    max_retries: int = 3
    default_retry_delay: int = 30

    log_labels: LogLabels = LogLabels.CELERY

    def get_celery_details(self) -> dict[str, t.Any]:
        return {
            "celery worker": self.request.hostname,
            "queue": (self.request.delivery_info or {}).get("routing_key"),
            "task id": self.request.id,
        }


def run_async_task[R](coroutine_factory: t.Callable[[], t.Awaitable[R]]) -> R:
    """Run an async task body in a new event loop and release db connections after."""

    async def _run() -> R:
        try:
            return await coroutine_factory()
        finally:
            await db_client.dispose()

    return asyncio.run(_run())
