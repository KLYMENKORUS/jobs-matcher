__all__ = ("AnalysisIterableTaskState",)

import typing as t

from ..._base.states import BaseIterableTaskState

if t.TYPE_CHECKING:
    from ..task import AnalysisTask


class AnalysisIterableTaskState(BaseIterableTaskState):
    def __init__(self, *, task: AnalysisTask) -> None:
        from .analyze_vacancies import AnalysisAnalyzeVacanciesState
        from .prefilter_vacancies import AnalysisPrefilterVacanciesState
        from .prepare_cvs import AnalysisPrepareCvsState

        super().__init__(
            AnalysisPrepareCvsState(task=task),
            AnalysisPrefilterVacanciesState(task=task),
            AnalysisAnalyzeVacanciesState(task=task),
        )
