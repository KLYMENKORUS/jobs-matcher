__all__ = ("SendingIterableTaskState",)

import typing as t

from ..._base.states import BaseIterableTaskState

if t.TYPE_CHECKING:
    from ..task import SendingTask


class SendingIterableTaskState(BaseIterableTaskState):
    def __init__(self, *, task: SendingTask) -> None:
        from .send_matches import SendingSendMatchesState

        super().__init__(
            SendingSendMatchesState(task=task),
        )
