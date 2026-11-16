__all__ = (
    "app",
    "parse_vacancies",
    "analyze_vacancies",
    "send_matches"
)

from app.infrastructure.database.service import UnitOfWork
from app.modules.workers.base import BaseTaskWithRetry, run_async_task
from app.modules.workers.jobs.celery_app import JobsCeleryApp, Queue
from app.shared.utils.logger import Logger

app = JobsCeleryApp()


@app.task(bind=True, base=BaseTaskWithRetry, queue=Queue.PARSING)  # type: ignore[untyped-decorator]
def parse_vacancies(self: BaseTaskWithRetry) -> bool:
    """Worker 1: collect new vacancies; on success, kick the analysis."""

    # ------------------------------------------------------------------------ #
    async def _process_task() -> bool:
        from app.modules.tasks.parsing.task import ParsingTask

        logger = Logger(name="parsing-worker", disable_stream_handler=False)
        logger.subinfo(f"[{self.log_labels}] start parsing ({self.get_celery_details()})")
        async with UnitOfWork() as uow:
            return await ParsingTask(
                logger=logger, uow=uow, celery_details=self.get_celery_details()
            ).run()
    # ------------------------------------------------------------------------ #

    if result := run_async_task(_process_task):
        analyze_vacancies.apply_async(queue=Queue.ANALYSIS)

    return result


@app.task(bind=True, base=BaseTaskWithRetry, queue=Queue.ANALYSIS)  # type: ignore[untyped-decorator]
def analyze_vacancies(self: BaseTaskWithRetry) -> bool:
    """Worker 2: score new vacancies for users; on success, kick the sending."""

    # ------------------------------------------------------------------------ #
    async def _process_task() -> bool:
        from app.modules.tasks.analysis.task import AnalysisTask

        logger = Logger(name="analysis-worker", disable_stream_handler=False)
        logger.subinfo(f"[{self.log_labels}] start analysis ({self.get_celery_details()})")
        async with UnitOfWork() as uow:
            return await AnalysisTask(
                logger=logger, uow=uow, celery_details=self.get_celery_details()
            ).run()
    # ------------------------------------------------------------------------ #

    if result := run_async_task(_process_task):
        send_matches.apply_async(queue=Queue.SENDING)
    return result


@app.task(bind=True, base=BaseTaskWithRetry, queue=Queue.SENDING)  # type: ignore[untyped-decorator]
def send_matches(self: BaseTaskWithRetry) -> bool:
    """Worker 3: send scored vacancies to users in Telegram."""

    # ------------------------------------------------------------------------ #
    async def _process_task() -> bool:
        from app.modules.tasks.sending.task import SendingTask

        logger = Logger(name="sending-worker", disable_stream_handler=False)
        logger.subinfo(f"[{self.log_labels}] start sending ({self.get_celery_details()})")
        async with UnitOfWork() as uow:
            return await SendingTask(
                logger=logger, uow=uow, celery_details=self.get_celery_details()
            ).run()
    # ------------------------------------------------------------------------ #

    return run_async_task(_process_task)
