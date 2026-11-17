__all__ = (
    "BaseTaskState",
    "BaseIterableTaskState",
)

import abc
import typing as t
from enum import IntEnum

if t.TYPE_CHECKING:
    from ..tasks import BaseProcessingTask


class BaseTaskState(abc.ABC):
    """
    One step of a task. A state must be safe to re-run: if the worker dies in
    the middle of it, the next run starts this same state again.
    """

    execution_status: t.ClassVar[IntEnum]

    def __init__(self, *, task: BaseProcessingTask[t.Any]) -> None:
        # ------------------------------------------------------------------------ #
        self.task: BaseProcessingTask[t.Any] = task
        # ------------------------------------------------------------------------ #

    @abc.abstractmethod
    async def run(self) -> None:
        pass


class BaseIterableTaskState(t.Iterable[BaseTaskState]):
    def __init__(self, *states: BaseTaskState) -> None:
        # ------------------------------------------------------------------------ #
        self._states: tuple[BaseTaskState, ...] = states
        # ------------------------------------------------------------------------ #

    def __iter__(self) -> t.Iterator[BaseTaskState]:
        yield from self._states
