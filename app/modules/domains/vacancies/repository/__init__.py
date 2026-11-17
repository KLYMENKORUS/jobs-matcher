__all__ = ("VacancyRepository",)

import typing as t
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import exists, func, select, update
from sqlalchemy.dialects.postgresql import insert

from app.infrastructure.database.crud import BaseCRUD
from app.modules.domains.interactions.models import UserVacancyInteraction
from app.modules.domains.vacancies.models import Vacancy, VacancyKeyword
from app.shared.utils.enums.domains.vacancies import VacancyStatus


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
        self, *, items: Sequence[dict[str, t.Any]]
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

    async def get_collected_until_map(
        self, *, sources: Sequence[str], keywords: Sequence[str]
    ) -> dict[tuple[str, str], datetime]:
        """
        (source, keyword) -> `posted_at` of the newest vacancy already collected
        by that search. Pairs never collected are missing from the result.
        """
        if not sources or not keywords:
            return {}

        query = (
            select(
                Vacancy.source,
                VacancyKeyword.keyword,
                func.max(Vacancy.posted_at),
            )
            .join(VacancyKeyword, VacancyKeyword.vacancy_id == Vacancy.id)
            .where(
                Vacancy.source.in_(sources),
                VacancyKeyword.keyword.in_(keywords),
                Vacancy.posted_at.is_not(None),
            )
            .group_by(Vacancy.source, VacancyKeyword.keyword)
        )
        rows = (await self.session.execute(query)).all()
        return {
            (source, keyword): until
            for source, keyword, until in rows
            if until is not None
        }

    async def get_ids_by_urls(self, *, urls: Sequence[str]) -> dict[str, int]:
        if not urls:
            return {}

        query = select(Vacancy.url, Vacancy.id).where(Vacancy.url.in_(urls))
        return {url: id for url, id in (await self.session.execute(query)).all()}

    async def link_keyword(
        self, *, vacancy_ids: Sequence[int], keyword: str
    ) -> None:
        """INSERT ... ON CONFLICT (vacancy_id, keyword) DO NOTHING"""
        if not vacancy_ids:
            return

        query = (
            insert(VacancyKeyword)
            .values(
                [
                    {"vacancy_id": vacancy_id, "keyword": keyword}
                    for vacancy_id in vacancy_ids
                ]
            )
            .on_conflict_do_nothing(constraint="uq_vacancy_keyword")
        )
        await self.session.execute(query)

    async def get_unprocessed_for_user(
        self,
        *,
        user_id: int,
        keywords: Sequence[str] | None = None,
        created_since: datetime | None = None,
        exclude_ids: Sequence[int] | None = None,
        status: VacancyStatus | None = None,
        limit: int | None = 50,
    ) -> Sequence[Vacancy]:
        """
        Vacancies the user has no interaction with yet.

        `keywords` - only vacancies found by one of them;
        `created_since` - skip the archive older than this;
        `exclude_ids` - skip vacancies that already failed in this run;
        `status` - only vacancies in this status (e.g. COLLECTED).
        """
        has_interaction = exists().where(
            UserVacancyInteraction.vacancy_id == Vacancy.id,
            UserVacancyInteraction.user_id == user_id,
        )
        query = select(Vacancy).where(~has_interaction)

        if keywords is not None:
            query = query.where(
                exists().where(
                    VacancyKeyword.vacancy_id == Vacancy.id,
                    VacancyKeyword.keyword.in_(keywords),
                )
            )
        if created_since is not None:
            query = query.where(Vacancy.created_at >= created_since)
        if exclude_ids:
            query = query.where(Vacancy.id.not_in(exclude_ids))
        if status is not None:
            query = query.where(Vacancy.status == status)

        query = query.order_by(Vacancy.created_at.desc()).limit(limit)
        return (await self.session.scalars(query)).all()

    async def get_by_status(
        self,
        *,
        status: VacancyStatus,
        sources: Sequence[str] | None = None,
        limit: int | None = 50,
    ) -> Sequence[Vacancy]:
        query = select(Vacancy).where(Vacancy.status == status)
        if sources is not None:
            query = query.where(Vacancy.source.in_(sources))

        query = query.order_by(Vacancy.id).limit(limit)
        return (await self.session.scalars(query)).all()

    async def update_details(self, *, id: int, values: dict[str, t.Any]) -> None:
        await self.session.execute(
            update(Vacancy).where(Vacancy.id == id).values(**values)
        )

    async def set_status(self, *, id: int, status: VacancyStatus) -> None:
        await self.session.execute(
            update(Vacancy).where(Vacancy.id == id).values(status=status)
        )
