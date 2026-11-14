__all__ = (
    "BaseAIClient",
    "AIRequest",
    "OutputT",
)

import abc
import functools
import typing as t

from pydantic import BaseModel
from pydantic_ai import Agent, AgentRunResult
from pydantic_ai.models import Model
from pydantic_ai.providers import Provider

from app.shared.utils.descriptors import RequiredTypedField
from app.shared.utils.exceptions.ai_client import AIRunFailedException

OutputT = t.TypeVar("OutputT", bound=BaseModel)


class AIRequest(BaseModel):
    system_prompt: str
    user_prompt: str


class BaseAIClient[T: BaseModel](abc.ABC):

    provider = RequiredTypedField(
        expected_type=Provider
    )
    model = RequiredTypedField(
        expected_type=Model
    )

    def __init__(self, *, output_type: type[T]) -> None:
        # ------------------------------------------------------------------------ #
        self.output_type: type[T] = output_type
        # ------------------------------------------------------------------------ #

    @staticmethod
    def run_failed_catch_wrapper[S, **P, R](
            function: t.Callable[t.Concatenate[S, P], t.Awaitable[R]]
    ) -> t.Callable[t.Concatenate[S, P], t.Coroutine[t.Any, t.Any, R]]:
        # ------------------------------------------------------------------------ #
        @functools.wraps(function)
        async def wrapper(self: S, /, *args: P.args, **kwargs: P.kwargs) -> R:
            try:
                return await function(self, *args, **kwargs)
            except Exception as exp:
                raise AIRunFailedException(
                    client_type=type(self).__name__,
                    reason=str(exp)
                ) from exp
        # ------------------------------------------------------------------------ #

        return wrapper

    @abc.abstractmethod
    def create_agent(self, *, system_prompt: str) -> Agent[None, T]:
        pass

    @abc.abstractmethod
    async def run(self, *, agent: Agent[None, T], request: AIRequest) -> AgentRunResult[T]:
        pass
