import traceback
from pathlib import Path

from app.modules.analyzer.cleaner import TextCleaner
from app.modules.domains.users import UserSchema
from app.shared.utils.enums.tasks import (
    AnalysisExecutionStatus as ExecutionStatus,
)
from app.shared.utils.logger.decorators import delimit_wrapper

from ..._base.states import BaseTaskState
from ..task import AnalysisTask


class AnalysisPrepareCvsState(BaseTaskState):
    """
    Parse and clean the CV of every active user once per run and snapshot it to
    `task_runs.details["cvs"]` ({user_id: text}). The next states read the
    snapshot, so the file is not parsed per vacancy and a resumed run analyses
    with the same CV.

    A user without a CV or with a broken file is left out: their interactions
    stay NEW and are analysed once the CV is fixed.
    """

    task: AnalysisTask
    execution_status = ExecutionStatus.PREPARE_CVS

    @delimit_wrapper(
        section="analysis",
        obj="prepare-cvs",
        detail="parse and clean users' cvs",
        is_subdelimit=True,
    )
    async def run(self) -> None:
        users: list[UserSchema] = await self.task.user_service.get_active_users()

        cvs = {
            str(user.id): cv
            for user in users
            if user.cv_file and (cv := await self._prepare(user=user))
        }
        await self.task.merge_details(cvs=cvs)

        self.task.logger.info(
            f"[{self.task.log_labels}] prepared cvs: {len(cvs)} of {len(users)} users"
        )

    async def _prepare(self, *, user: UserSchema) -> str | None:
        try:
            raw: str = await self.task.cv_parser.parse(path=Path(str(user.cv_file)))
        except Exception:  # noqa
            self.task.logger.error(
                f"[{self.task.log_labels}] user (id: {user.id}): cv parsing failed\n"
                f"{traceback.format_exc()}"
            )
            return None

        cv: str = TextCleaner.clean_cv(raw, max_chars=self.task.MAX_CV_CHARS)
        self.task.logger.detail(
            f"[{self.task.log_labels}] user (id: {user.id}): cv {len(raw)} -> {len(cv)} chars"
        )
        return cv or None
