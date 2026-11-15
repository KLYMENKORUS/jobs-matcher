__all__ = (
    "VacancyRepository",
    "InteractionRepository"
)

import typing as t
from collections.abc import Sequence

from sqlalchemy import exists, select
from sqlalchemy.dialects.postgresql import insert

from app.infrastructure.database.crud import BaseCRUD
from app.modules.domains.vacancies.models import UserVacancyInteraction, Vacancy
from app.shared.utils.enums.domains.vacancies import InteractionStatus


class VacancyRepository(BaseCRUD[Vacancy]):
    model = Vacancy

    async def get_by_url(self, *, url: str) -> Vacancy | None:
        query = select(Vacancy).where(Vacancy.url == url)
        return await self.session.scalar(query)

    async def get_existing_urls(self, *, urls: Sequence[str]) -> set[str]:
        if not urls:
            return set()

        query = select(Vacancy.url).where(Vacancy.url.in_(urls))
        return set((await self.session.scalars(query)).all())

    async def create_many_skip_existing(
            self,
            *,
            items: Sequence[dict[str, t.Any]]
    ) -> Sequence[Vacancy]:
        """INSERT ... ON CONFLICT (url) DO NOTHING"""
        if not items:
            return []

        query = (
            insert(Vacancy)
            .values(list(items))
            .on_conflict_do_nothing(index_elements=[Vacancy.url])
            .returning(Vacancy)
        )
        return (await self.session.scalars(query)).all()

    async def get_unprocessed_for_user(
            self,
            *,
            user_id: int,
            limit: int | None = 50
    ) -> Sequence[Vacancy]:
        has_interaction = exists().where(
            UserVacancyInteraction.vacancy_id == Vacancy.id,
            UserVacancyInteraction.user_id == user_id,
        )
        query = (
            select(Vacancy)
            .where(~has_interaction)
            .order_by(Vacancy.created_at.desc())
            .limit(limit)
        )
        return (await self.session.scalars(query)).all()


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
