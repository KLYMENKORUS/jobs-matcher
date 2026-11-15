__all__ = (
    "VacancyCreateSchema",
    "VacancySchema",
    "VacancyMatchSchema",
    "InteractionSchema",
    "InteractionWithVacancySchema"
)

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.shared.utils.enums.domains.vacancies import InteractionStatus, VacancySource


# [vacancy]
################################################################################
class VacancyCreateSchema(BaseModel):
    title: str = Field(max_length=255)
    company: str | None = Field(default=None, max_length=255)
    description: str
    url: str = Field(max_length=512)
    source: VacancySource


class VacancySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    company: str | None
    description: str
    url: str
    source: str
    created_at: datetime
################################################################################


# [gemini]
################################################################################
class VacancyMatchSchema(BaseModel):
    match_score: float = Field(ge=0, le=100)
    match_reasoning: str
################################################################################


# [interaction]
################################################################################
class InteractionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    vacancy_id: int
    match_score: float | None
    match_reasoning: str | None
    status: InteractionStatus


class InteractionWithVacancySchema(InteractionSchema):
    vacancy: VacancySchema
################################################################################
