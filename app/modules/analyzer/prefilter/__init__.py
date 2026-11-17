__all__ = ("VacancyPrefilter",)

import re
import typing as t
from collections.abc import Sequence

from app.modules.domains.vacancies.schemas import VacancySchema


class VacancyPrefilter:
    """
    Cheap checks before the AI: a vacancy that fails one is rejected without
    spending tokens on it. Returns the reason (shown as `match_reasoning`).

    - the vacancy has (almost) no text - nothing for the AI to compare;
    - none of the user's keywords is in the title / description: the sources'
      search is fuzzy and returns vacancies that only mention a related word.
    """
    MIN_TEXT_CHARS: t.Final[int] = 150

    def check(self, *, vacancy: VacancySchema, keywords: Sequence[str]) -> str | None:
        text: str = f"{vacancy.title or ''}\n{vacancy.description or ''}".strip()

        if len(text) < self.MIN_TEXT_CHARS:
            return "Префільтр: у вакансії майже немає опису."

        if keywords and not any(self._contains(text, keyword) for keyword in keywords):
            return (
                "Префільтр: у вакансії немає жодного ключового слова "
                f"({', '.join(keywords)})."
            )

        return None

    @staticmethod
    def _contains(text: str, keyword: str) -> bool:
        pattern: str = rf"(?<!\w){re.escape(keyword.strip())}(?!\w)"
        return re.search(pattern, text, re.IGNORECASE) is not None
