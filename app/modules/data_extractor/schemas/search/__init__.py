__all__ = ("VacanciesSearchResults",)

from pydantic import BaseModel, Field

from ..vacancy import VacancyMain


class VacanciesSearchResults(BaseModel):
    results: list[VacancyMain] = Field(default_factory=list)
    total: int | None = Field(default=None)
