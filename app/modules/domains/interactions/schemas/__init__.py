__all__ = (
    "VacancyMatchSchema",
    "InteractionSchema",
    "InteractionWithVacancySchema",
)

from pydantic import BaseModel, ConfigDict, Field

from app.modules.domains.vacancies.schemas import VacancySchema
from app.shared.utils.enums.domains.interactions import InteractionStatus


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
