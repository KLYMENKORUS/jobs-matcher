__all__ = ("VacancyMatchAnalyzer",)

import textwrap
import typing as t

from pydantic_ai import Agent

from app.clients.ai_client.base import AIRequest, BaseAIClient
from app.clients.ai_client.gemini import GeminiAIClient
from app.modules.domains.interactions.schemas import VacancyMatchSchema
from app.modules.domains.vacancies.schemas import VacancySchema


class VacancyMatchAnalyzer:
    SYSTEM_PROMPT: t.Final[str] = textwrap.dedent(
        """
        You are an experienced technical recruiter. Compare the candidate's CV with
        the vacancy and estimate how well the candidate fits it.

        Return:
        - match_score: a number from 0 to 100, where
            90-100 - strong fit, meets almost every requirement;
            70-89  - good fit, worth applying;
            40-69  - partial fit, important gaps;
            0-39   - poor fit or a different profession / seniority.
        - match_reasoning: 2-4 short sentences in Ukrainian - the main reasons for
          the score: matching skills, missing requirements, seniority, location.

        Judge only by the given texts, do not invent facts about the candidate.
        """
    ).strip()

    # long descriptions are cut, the beginning carries the requirements
    MAX_DESCRIPTION_CHARS: t.Final[int] = 8000
    MAX_CV_CHARS: t.Final[int] = 8000

    def __init__(self, *, ai_client: BaseAIClient[VacancyMatchSchema] | None = None) -> None:
        # ------------------------------------------------------------------------ #
        self._ai_client: BaseAIClient[VacancyMatchSchema] = (
            ai_client or GeminiAIClient(output_type=VacancyMatchSchema)
        )
        # ------------------------------------------------------------------------ #
        self._agent: Agent[None, VacancyMatchSchema] = self._ai_client.create_agent(
            system_prompt=self.SYSTEM_PROMPT
        )
        # ------------------------------------------------------------------------ #

    async def analyze(self, *, cv_text: str, vacancy: VacancySchema) -> VacancyMatchSchema:
        result = await self._ai_client.run(
            agent=self._agent,
            request=AIRequest(
                system_prompt=self.SYSTEM_PROMPT,
                user_prompt=self._build_user_prompt(cv_text=cv_text, vacancy=vacancy),
            ),
        )
        return result.output

    def _build_user_prompt(self, *, cv_text: str, vacancy: VacancySchema) -> str:
        return "\n".join(
            [
                "# Candidate CV",
                cv_text[: self.MAX_CV_CHARS],
                "",
                "# Vacancy",
                f"Title: {vacancy.title or '-'}",
                f"Company: {vacancy.company or '-'}",
                f"Source: {vacancy.source}",
                "Description:",
                (vacancy.description or "")[: self.MAX_DESCRIPTION_CHARS],
            ]
        )
