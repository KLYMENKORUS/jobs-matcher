__all__ = ("ParsingIterableTaskState",)

import typing as t

from ..._base.states import BaseIterableTaskState

if t.TYPE_CHECKING:
    from ..task import ParsingTask


class ParsingIterableTaskState(BaseIterableTaskState):
    def __init__(self, *, task: ParsingTask) -> None:
        from .collect_vacancy_details import ParsingCollectVacancyDetailsState
        from .collect_vacancy_urls import ParsingCollectVacancyUrlsState
        from .link_vacancies_to_users import ParsingLinkVacanciesToUsersState
        from .prepare_search_queries import ParsingPrepareSearchQueriesState

        super().__init__(
            ParsingPrepareSearchQueriesState(task=task),
            ParsingCollectVacancyUrlsState(task=task),
            ParsingCollectVacancyDetailsState(task=task),
            ParsingLinkVacanciesToUsersState(task=task),
        )
