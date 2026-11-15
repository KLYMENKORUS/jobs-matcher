__all__ = ("InteractionService",)

import typing as t
from collections.abc import Sequence
from datetime import datetime

from app.infrastructure.database.service import UnitOfWork
from app.modules.domains.interactions.models import UserVacancyInteraction
from app.modules.domains.interactions.schemas import (
    InteractionSchema,
    InteractionWithVacancySchema,
    VacancyMatchSchema,
)
from app.shared.utils.enums.domains.interactions import InteractionStatus
from app.shared.utils.enums.domains.vacancies import VacancyStatus
from app.shared.utils.exceptions.domains.interactions import InteractionNotFoundError


class InteractionService:
    """A vacancy for a user: linking, AI score and delivery status."""

    def __init__(self, *, uow_factory: t.Callable[[], UnitOfWork] = UnitOfWork) -> None:
        # ------------------------------------------------------------------------ #
        self._uow_factory: t.Callable[[], UnitOfWork] = uow_factory
        # ------------------------------------------------------------------------ #

    # [link]
    ################################################################################
    async def link_to_user(
            self, *,
            user_id: int,
            keywords: Sequence[str],
            created_since: datetime | None = None
    ) -> int:
        """
        Create NEW interactions for COLLECTED vacancies found by the user's
        keywords that the user has no interaction with yet.
        Returns how many vacancies were linked.
        """
        async with self._uow_factory() as uow:
            vacancies = await uow.vacancies.get_unprocessed_for_user(
                user_id=user_id,
                keywords=keywords,
                created_since=created_since,
                status=VacancyStatus.COLLECTED,
                limit=None,
            )
            linked: int = await uow.interactions.create_new_many(
                user_id=user_id, vacancy_ids=[vacancy.id for vacancy in vacancies]
            )
            await uow.commit()

        return linked

    async def get_new_interactions(
            self, *,
            user_id: int,
            exclude_ids: Sequence[int] | None = None,
            limit: int | None = 20
    ) -> list[InteractionWithVacancySchema]:
        """Interactions linked to the user and not analysed yet."""
        async with self._uow_factory() as uow:
            interactions = await uow.interactions.get_new_for_user(
                user_id=user_id, exclude_ids=exclude_ids, limit=limit
            )
            return [InteractionWithVacancySchema.model_validate(item) for item in interactions]

    async def set_match(self, *, interaction_id: int, match: VacancyMatchSchema) -> bool:
        """Save the AI score: NEW -> PENDING."""
        async with self._uow_factory() as uow:
            updated: bool = await uow.interactions.set_match(
                id=interaction_id,
                match_score=match.match_score,
                match_reasoning=match.match_reasoning,
            )
            await uow.commit()

        return updated

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
