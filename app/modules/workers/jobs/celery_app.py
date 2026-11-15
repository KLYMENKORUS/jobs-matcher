__all__ = (
    "JobsCeleryApp",
    "Queue",
)

from datetime import timedelta
from enum import StrEnum

from app.modules.workers.base import BaseCeleryApp
from app.shared.settings import settings


class Queue(StrEnum):
    PARSING = "parsing"
    ANALYSIS = "analysis"
    SENDING = "sending"


class JobsCeleryApp(BaseCeleryApp):
    """
    One app, three queues - run one worker per queue:

        celery -A app.modules.workers.jobs.tasks worker -Q parsing  -c 1 -n parsing@%h
        celery -A app.modules.workers.jobs.tasks worker -Q analysis -c 1 -n analysis@%h
        celery -A app.modules.workers.jobs.tasks worker -Q sending  -c 1 -n sending@%h
        celery -A app.modules.workers.jobs.tasks beat
    """

    TASKS_MODULE: str = "app.modules.workers.jobs.tasks"

    def __init__(self) -> None:
        super().__init__(main="jobs_worker", broker=settings.BROKER_URL)

        # [routing]
        # ------------------------------------------------------------------------ #
        self.conf.task_routes = {
            f"{self.TASKS_MODULE}.parse_vacancies": {"queue": Queue.PARSING},
            f"{self.TASKS_MODULE}.analyze_vacancies": {"queue": Queue.ANALYSIS},
            f"{self.TASKS_MODULE}.send_matches": {"queue": Queue.SENDING},
        }
        # ------------------------------------------------------------------------ #

        # [cron settings]
        # ------------------------------------------------------------------------ #
        self.conf.beat_schedule = {
            "parse-vacancies": {
                "task": f"{self.TASKS_MODULE}.parse_vacancies",
                "schedule": timedelta(minutes=settings.PARSING_INTERVAL_MINUTES),
                "options": {
                    "queue": Queue.PARSING,
                    "expires": settings.PARSING_INTERVAL_MINUTES * 60,
                },
            },
            "analyze-vacancies": {
                "task": f"{self.TASKS_MODULE}.analyze_vacancies",
                "schedule": timedelta(minutes=settings.ANALYSIS_INTERVAL_MINUTES),
                "options": {
                    "queue": Queue.ANALYSIS,
                    "expires": settings.ANALYSIS_INTERVAL_MINUTES * 60,
                },
            },
            "send-matches": {
                "task": f"{self.TASKS_MODULE}.send_matches",
                "schedule": timedelta(minutes=settings.SENDING_INTERVAL_MINUTES),
                "options": {
                    "queue": Queue.SENDING,
                    "expires": settings.SENDING_INTERVAL_MINUTES * 60,
                },
            }
        }
        # ------------------------------------------------------------------------ #
