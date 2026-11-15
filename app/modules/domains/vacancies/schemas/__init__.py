__all__ = (
    "VacancyCreateSchema",
    "VacancySchema",
)

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.shared.utils.enums.domains.vacancies import VacancySource, VacancyStatus


# [vacancy]
################################################################################
class VacancyCreateSchema(BaseModel):
    """
    A vacancy to save. Only `url` + `source` (+ `posted_at`) are required, which
    is what a search page that lists links gives: such a vacancy is saved as NEW
    and its details are collected later. A search that returns full data saves
    it as COLLECTED right away.
    """
    url: str = Field(max_length=512)
    source: VacancySource
    posted_at: datetime | None = Field(default=None)
    title: str | None = Field(default=None, max_length=255)
    company: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None)
    status: VacancyStatus = Field(default=VacancyStatus.NEW)


class VacancySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str | None
    company: str | None
    description: str | None
    url: str
    source: str
    status: VacancyStatus
    posted_at: datetime | None = None
    created_at: datetime
################################################################################
