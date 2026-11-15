__all__ = ("InteractionRepository",)

from collections.abc import Sequence

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from app.infrastructure.database.crud import BaseCRUD
from app.modules.domains.interactions.models import UserVacancyInteraction
from app.shared.utils.enums.domains.interactions import InteractionStatus


class InteractionRepository(BaseCRUD[UserVacancyInteraction]):
    model = UserVacancyInteraction

    async def get_by_user_and_vacancy(
            self,
            *,
            user_id: int,
            vacancy_id: int
    ) -> UserVacancyInteraction | None:
        query = select(UserVacancyInteraction).where(
            UserVacancyInteraction.user_id == user_id,
            UserVacancyInteraction.vacancy_id == vacancy_id,
        )
        return await self.session.scalar(query)

    async def upsert_match(
            self,
            *,
            user_id: int,
            vacancy_id: int,
            match_score: float,
            match_reasoning: str
    ) -> UserVacancyInteraction:
        query = (
            insert(UserVacancyInteraction)
            .values(
                user_id=user_id,
                vacancy_id=vacancy_id,
                match_score=match_score,
                match_reasoning=match_reasoning,
                status=InteractionStatus.PENDING,
            )
            .on_conflict_do_update(
                constraint="uq_user_vacancy",
                set_={"match_score": match_score, "match_reasoning": match_reasoning},
            )
            .returning(UserVacancyInteraction)
        )
        return (await self.session.scalars(query)).one()

    async def create_new_many(self, *, user_id: int, vacancy_ids: Sequence[int]) -> int:
        """Link vacancies to the user as NEW interactions; returns how many were created."""
        if not vacancy_ids:
            return 0

        query = (
            insert(UserVacancyInteraction)
            .values([
                {"user_id": user_id, "vacancy_id": vacancy_id, "status": InteractionStatus.NEW}
                for vacancy_id in vacancy_ids
            ])
            .on_conflict_do_nothing(constraint="uq_user_vacancy")
            .returning(UserVacancyInteraction.id)
        )
        return len((await self.session.scalars(query)).all())

    async def get_new_for_user(
            self,
            *,
            user_id: int,
            exclude_ids: Sequence[int] | None = None,
            limit: int | None = 20
    ) -> Sequence[UserVacancyInteraction]:
        query = select(UserVacancyInteraction).where(
            UserVacancyInteraction.user_id == user_id,
            UserVacancyInteraction.status == InteractionStatus.NEW,
        )
        if exclude_ids:
            query = query.where(UserVacancyInteraction.id.not_in(exclude_ids))

        query = query.order_by(UserVacancyInteraction.id).limit(limit)
        return (await self.session.scalars(query)).all()

    async def set_match(
            self, *, id: int, match_score: float, match_reasoning: str
    ) -> bool:
        """NEW -> PENDING with the AI score; False if it was not NEW anymore."""
        query = (
            update(UserVacancyInteraction)
            .where(
                UserVacancyInteraction.id == id,
                UserVacancyInteraction.status == InteractionStatus.NEW,
            )
            .values(
                match_score=match_score,
                match_reasoning=match_reasoning,
                status=InteractionStatus.PENDING,
            )
            .returning(UserVacancyInteraction.id)
        )
        return await self.session.scalar(query) is not None

    async def get_by_status(
            self,
            *,
            user_id: int,
            status: InteractionStatus,
            min_score: float | None = None,
            limit: int | None = 20
    ) -> Sequence[UserVacancyInteraction]:
        query = select(UserVacancyInteraction).where(
            UserVacancyInteraction.user_id == user_id,
            UserVacancyInteraction.status == status,
        )
        if min_score is not None:
            query = query.where(UserVacancyInteraction.match_score >= min_score)

        query = query.order_by(UserVacancyInteraction.match_score.desc().nulls_last()).limit(limit)
        return (await self.session.scalars(query)).all()
