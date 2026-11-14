__all__ = ("GeminiAIClient",)

from http import HTTPStatus

from google.genai.types import HttpRetryOptions, ThinkingLevel
from pydantic import BaseModel
from pydantic_ai import Agent, AgentRunResult
from pydantic_ai.models.google import GoogleModel, GoogleModelSettings
from pydantic_ai.providers.google import GoogleProvider

from app.shared.settings import settings

from ..base import AIRequest, BaseAIClient


class GeminiAIClient[T: BaseModel](BaseAIClient[T]):
    retry_options = HttpRetryOptions(
        attempts=5,
        initial_delay=1.0,
        max_delay=60.0,
        http_status_codes=[
            HTTPStatus.REQUEST_TIMEOUT,
            HTTPStatus.TOO_MANY_REQUESTS,
            HTTPStatus.INTERNAL_SERVER_ERROR,
            HTTPStatus.BAD_GATEWAY,
            HTTPStatus.SERVICE_UNAVAILABLE,
            HTTPStatus.GATEWAY_TIMEOUT
        ]
    )

    def __init__(self, *, output_type: type[T]) -> None:
        super().__init__(output_type=output_type)

        # [main]
        # ------------------------------------------------------------------------ #
        self.provider: GoogleProvider = (
            GoogleProvider(
                api_key=settings.AI_API_KEY,
                retry_options=self.retry_options
            )
        )

        # [model settings]
        # ------------------------------------------------------------------------ #
        self.model: GoogleModel = (
            GoogleModel(
                model_name=settings.AI_MODEL_NAME,
                provider=self.provider,
                settings=(
                    GoogleModelSettings(
                        google_thinking_config={
                            "include_thoughts": False,
                            "thinking_level": ThinkingLevel.MEDIUM
                        }
                    )
                )
            )
        )
        # ------------------------------------------------------------------------ #

    def create_agent(self, *, system_prompt: str) -> Agent[None, T]:
        return Agent(
            model=self.model,
            output_type=self.output_type,
            instructions=system_prompt,
            retries=2
        )

    @BaseAIClient.run_failed_catch_wrapper
    async def run(self, *, agent: Agent[None, T], request: AIRequest) -> AgentRunResult[T]:
        return await agent.run(user_prompt=request.user_prompt)
