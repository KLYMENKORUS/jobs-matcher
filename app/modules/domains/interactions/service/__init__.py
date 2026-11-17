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
from app.shared.utils.exceptions.domains.interactions import (
    InteractionNotFoundError,
)


class InteractionService:
    """A vacancy for a user: linking, AI score and delivery status."""

    def __init__(
        self, *, uow_factory: t.Callable[[], UnitOfWork] = UnitOfWork
    ) -> None:
        # ------------------------------------------------------------------------ #
        self._uow_factory: t.Callable[[], UnitOfWork] = uow_factory
        # ------------------------------------------------------------------------ #

    # [link]
    ################################################################################
    async def link_to_user(
        self,
        *,
        user_id: int,
        keywords: Sequence[str],
        created_since: datetime | None = None,
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
                user_id=user_id,
                vacancy_ids=[vacancy.id for vacancy in vacancies],
            )
            await uow.commit()

        return linked

    async def get_new_interactions(
        self,
        *,
        user_id: int,
        exclude_ids: Sequence[int] | None = None,
        limit: int | None = 20,
    ) -> list[InteractionWithVacancySchema]:
        """Interactions linked to the user and not analysed yet."""
        async with self._uow_factory() as uow:
            interactions = await uow.interactions.get_new_for_user(
                user_id=user_id, exclude_ids=exclude_ids, limit=limit
            )
            return [
                InteractionWithVacancySchema.model_validate(item)
                for item in interactions
            ]

    async def set_match(
        self, *, interaction_id: int, match: VacancyMatchSchema
    ) -> bool:
        """Save the AI score: NEW -> PENDING (min_score is applied when sending)."""
        async with self._uow_factory() as uow:
            updated: bool = await uow.interactions.set_match(
                id=interaction_id,
                match_score=match.match_score,
                match_reasoning=match.match_reasoning,
            )
            await uow.commit()

        return updated

    async def copy_twin_match(
        self, *, interaction: InteractionWithVacancySchema
    ) -> bool:
        """
        If the user already has this vacancy scored from another source (same
        title + company), copy that score: NEW -> PENDING without the AI. The
        copy is sent like any other match, so the user gets the vacancy from
        every source. False if there is no twin (or title / company is unknown).
        """
        vacancy = interaction.vacancy
        if not vacancy.title or not vacancy.company:
            return False

        async with self._uow_factory() as uow:
            twin: (
                UserVacancyInteraction | None
            ) = await uow.interactions.get_scored_twin(
                user_id=interaction.user_id,
                title=vacancy.title,
                company=vacancy.company,
            )

            if twin is None or twin.match_score is None:
                return False

            updated: bool = await uow.interactions.set_match(
                id=interaction.id,
                match_score=twin.match_score,
                match_reasoning=twin.match_reasoning or "",
            )
            await uow.commit()

        return updated

    async def reject(self, *, interaction_ids: Sequence[int], reason: str) -> int:
        """NEW -> REJECTED without asking the AI (prefilter)."""
        async with self._uow_factory() as uow:
            rejected: int = await uow.interactions.reject_new_many(
                ids=interaction_ids, reason=reason
            )
            await uow.commit()

        return rejected

    async def save_match(
        self, *, user_id: int, vacancy_id: int, match: VacancyMatchSchema
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
        self, *, user_id: int, min_score: float, limit: int | None = 20
    ) -> list[InteractionWithVacancySchema]:
        """
        PENDING with score >= the user's current min_score, best first. Below
        the threshold they just wait: lowering min_score makes them sendable.
        """
        async with self._uow_factory() as uow:
            interactions = await uow.interactions.get_by_status(
                user_id=user_id,
                status=InteractionStatus.PENDING,
                min_score=min_score,
                limit=limit,
            )
            return [
                InteractionWithVacancySchema.model_validate(item)
                for item in interactions
            ]

    async def react(self, *, callback: t.Any, telegram_id: int) -> bool:
        """
        Save the user's button reaction (APPLIED / SKIPPED) to a sent vacancy.
        False if the interaction is not the user's or was not sent; pressing
        the other button later just switches the status.
        """
        async with self._uow_factory() as uow:
            updated: bool = await uow.interactions.set_reaction(
                id=callback.interaction_id,
                telegram_id=telegram_id,
                status=callback.status,
            )
            await uow.commit()

        return updated

    async def update_status(
        self, *, interaction_id: int, status: InteractionStatus
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
