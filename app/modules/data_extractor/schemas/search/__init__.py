__all__ = (
    "VacancySearchItem",
    "VacanciesSearchResults",
)

import datetime as dt

from pydantic import BaseModel, Field

from app.modules.domains.vacancies.schemas import VacancyCreateSchema
from app.shared.utils.enums.domains.vacancies import VacancySource

from .._base import HttpUrlStr
from ..vacancy import VacancyMain


class VacancySearchItem(BaseModel):
    """
    One vacancy found by a search.

    Sources whose search page only lists links return `url` (+ `posted_at`) and
    leave `main` empty, the details are collected later by `vacancy.extract_main`.
    Sources whose search already returns full data (thejob) fill `main` too.
    """

    url: HttpUrlStr
    source: VacancySource
    posted_at: dt.datetime | None = Field(default=None)
    main: VacancyMain | None = Field(default=None)

    def to_create_schema(self) -> VacancyCreateSchema:
        if self.main is not None:
            return self.main.to_create_schema()

        return VacancyCreateSchema(
            url=self.url, source=self.source, posted_at=self.posted_at
        )


class VacanciesSearchResults(BaseModel):
    results: list[VacancySearchItem] = Field(default_factory=list)
    total: int | None = Field(default=None)
