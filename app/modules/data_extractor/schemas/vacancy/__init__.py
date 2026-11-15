__all__ = (
    "VacancyLocation",
    "VacancyMain",
    "VacancySalary",
)

import datetime as dt

from pydantic import BaseModel, Field

from app.modules.domains.vacancies.schemas import VacancyCreateSchema
from app.shared.utils.enums.domains.vacancies import VacancySource

from .._base import HttpUrlStr


class VacancySalary(BaseModel):
    min: float | None = Field(default=None)
    max: float | None = Field(default=None)
    currency: str | None = Field(default=None)
    period: str | None = Field(default=None)


class VacancyLocation(BaseModel):
    country: str | None = Field(default=None)
    city: str | None = Field(default=None)
    work_mode: str | None = Field(default=None)


class VacancyMain(BaseModel):
    url: HttpUrlStr
    source: VacancySource
    external_id: str | None = Field(default=None)

    title: str
    company: str | None = Field(default=None)
    summary: str | None = Field(default=None)
    description: str = Field(default_factory=str)

    salary: VacancySalary | None = Field(default=None)
    locations: list[VacancyLocation] = Field(default_factory=list)
    is_remote: bool = Field(default=False)

    experience_levels: list[str] = Field(default_factory=list)
    employment_types: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)

    posted_at: dt.datetime | None = Field(default=None)

    def to_create_schema(self) -> VacancyCreateSchema:
        """Map onto the vacancies domain, ready for `VacancyService`."""
        return VacancyCreateSchema(
            title=self.title,
            company=self.company if self.company else None,
            description=self.description,
            url=self.url,
            source=self.source,
        )
