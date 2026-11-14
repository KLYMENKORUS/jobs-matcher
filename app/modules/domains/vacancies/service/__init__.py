__all__ = ("VacancyService",)

import typing as t
from collections.abc import Sequence

from app.infrastructure.database.service import UnitOfWork
from app.modules.domains.vacancies.enums import InteractionStatus
from app.modules.domains.vacancies.models import UserVacancyInteraction
from app.modules.domains.vacancies.schemas import (
    InteractionSchema,
    InteractionWithVacancySchema,
    VacancyCreateSchema,
    VacancyMatchSchema,
    VacancySchema,
)
from app.shared.utils.exceptions.domains.vacancies import InteractionNotFoundError
from app.shared.utils.logger.decorators import delimit_wrapper


class VacancyService:

    def __init__(self, *, uow_factory: t.Callable[[], UnitOfWork] = UnitOfWork) -> None:
        # ------------------------------------------------------------------------ #
        self._uow_factory: t.Callable[[], UnitOfWork] = uow_factory
        # ------------------------------------------------------------------------ #

    # [vacancies]
    ################################################################################
    @delimit_wrapper(section="vacancies", obj="service", detail="save vacancies")
    async def save_vacancies(
            self, *, vacancies: Sequence[VacancyCreateSchema]
    ) -> list[VacancySchema]:
        # ------------------------------------------------------------------------ #
        unique: dict[str, VacancyCreateSchema] = {item.url: item for item in vacancies}
        if not unique:
            return []
        # ------------------------------------------------------------------------ #

        async with self._uow_factory() as uow:
            created = await uow.vacancies.create_many_skip_existing(
                items=[item.model_dump(mode="json") for item in unique.values()]
            )
            await uow.commit()

        return [VacancySchema.model_validate(vacancy) for vacancy in created]

    async def get_unprocessed_for_user(
            self, *,
            user_id: int,
            limit: int | None = 50
    ) -> list[VacancySchema]:
        async with self._uow_factory() as uow:
            vacancies = await uow.vacancies.get_unprocessed_for_user(
                user_id=user_id, limit=limit
            )
            return [VacancySchema.model_validate(vacancy) for vacancy in vacancies]
    ################################################################################

    # [interactions]
    ################################################################################
    async def save_match(
            self,
            *,
            user_id: int,
            vacancy_id: int,
            match: VacancyMatchSchema
    ) -> InteractionSchema:
        async with self._uow_factory() as uow:
            interaction = await uow.interactions.upsert_match(
                user_id=user_id,
                vacancy_id=vacancy_id,
                match_score=match.match_score,
                match_reasoning=match.match_reasoning,
            )
            await uow.commit()

        return InteractionSchema.model_validate(interaction)

    async def get_matches_to_send(
            self,
            *,
            user_id: int,
            min_score: float = 70,
            limit: int | None = 20
    ) -> list[InteractionWithVacancySchema]:
        async with self._uow_factory() as uow:
            interactions = await uow.interactions.get_by_status(
                user_id=user_id,
                status=InteractionStatus.PENDING,
                min_score=min_score,
                limit=limit,
            )
            return [InteractionWithVacancySchema.model_validate(item) for item in interactions]

    async def update_status(
            self,
            *,
            interaction_id: int,
            status: InteractionStatus
    ) -> InteractionSchema:
        async with self._uow_factory() as uow:
            interaction: UserVacancyInteraction | None = await uow.interactions.get(
                id=interaction_id
            )
            if interaction is None:
                raise InteractionNotFoundError(interaction_id=interaction_id)

            interaction.status = status
            await uow.commit()

        return InteractionSchema.model_validate(interaction)
    ################################################################################
