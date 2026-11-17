from app.shared.utils.enums.tasks import (
    ParsingExecutionStatus as ExecutionStatus,
)
from app.shared.utils.logger.decorators import delimit_wrapper

from ..._base.states import BaseTaskState
from ..task import ParsingTask


class ParsingPrepareSearchQueriesState(BaseTaskState):
    """
    Snapshot what this run searches: sources and unique keywords of active users,
    saved in `task_runs.details`. A resumed run searches the same set even if
    users changed their keywords in the meantime.
    """

    task: ParsingTask
    execution_status = ExecutionStatus.PREPARE_SEARCH_QUERIES

    @delimit_wrapper(
        section="parsing",
        obj="prepare-search-queries",
        detail="snapshot sources and keywords",
        is_subdelimit=True,
    )
    async def run(self) -> None:
        # ------------------------------------------------------------------------ #
        keywords: list[
            str
        ] = await self.task.user_settings_service.get_unique_active_keywords()
        sources: list[str] = [
            str(source) for source in self.task.extractor_factory.available_sources()
        ]
        # ------------------------------------------------------------------------ #

        await self.task.merge_details(sources=sources, keywords=keywords)

        if not keywords:
            self.task.logger.warning(
                f"[{self.task.log_labels}] no active users with keywords, nothing to parse"
            )
            return

        self.task.logger.info(
            f"[{self.task.log_labels}] prepared {len(sources) * len(keywords)} searches "
            f"({len(sources)} sources x {len(keywords)} keywords)"
        )
