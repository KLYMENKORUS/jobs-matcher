__all__ = ("VacancyService",)

import typing as t
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from app.infrastructure.database.service import UnitOfWork
from app.modules.domains.vacancies.schemas import VacancyCreateSchema, VacancySchema
from app.shared.settings import settings
from app.shared.utils.enums.domains.vacancies import VacancyStatus
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
                items=[item.model_dump() for item in unique.values()]
            )
            await uow.commit()

        return [VacancySchema.model_validate(vacancy) for vacancy in created]

    async def save_search_results(
            self, *, keyword: str, vacancies: Sequence[VacancyCreateSchema]
    ) -> int:
        """
        Save one (source, keyword) search in a single transaction: new vacancies
        plus the keyword link for every found vacancy (new and already known).

        The link is what moves the search's `collected_until`, so vacancies and
        the "how far collected" mark are always saved together.
        Returns how many vacancies were newly inserted.
        """
        unique: dict[str, VacancyCreateSchema] = {item.url: item for item in vacancies}
        if not unique:
            return 0

        async with self._uow_factory() as uow:
            created = await uow.vacancies.create_many_skip_existing(
                items=[item.model_dump() for item in unique.values()]
            )
            vacancy_ids: dict[str, int] = await uow.vacancies.get_ids_by_urls(
                urls=list(unique)
            )
            await uow.vacancies.link_keyword(
                vacancy_ids=list(vacancy_ids.values()), keyword=keyword
            )
            await uow.commit()

        return len(created)

    async def get_collected_until(
            self, *, sources: Sequence[str], keywords: Sequence[str]
    ) -> dict[tuple[str, str], datetime]:
        """
        (source, keyword) -> date the next search stops at: `posted_at` of the
        newest collected vacancy, or `now - PARSING_LOOKBACK_DAYS` for a new pair.
        """
        async with self._uow_factory() as uow:
            found = await uow.vacancies.get_collected_until_map(
                sources=sources, keywords=keywords
            )

        default: datetime = (
            datetime.now(UTC) - timedelta(days=settings.PARSING_LOOKBACK_DAYS)
        )
        return {
            (source, keyword): found.get((source, keyword), default)
            for source in sources
            for keyword in keywords
        }

    async def get_unprocessed_for_user(
            self, *,
            user_id: int,
            keywords: Sequence[str] | None = None,
            created_since: datetime | None = None,
            exclude_ids: Sequence[int] | None = None,
            limit: int | None = 50
    ) -> list[VacancySchema]:
        async with self._uow_factory() as uow:
            vacancies = await uow.vacancies.get_unprocessed_for_user(
                user_id=user_id,
                keywords=keywords,
                created_since=created_since,
                exclude_ids=exclude_ids,
                limit=limit,
            )
            return [VacancySchema.model_validate(vacancy) for vacancy in vacancies]

    async def get_by_status(
            self, *,
            status: VacancyStatus,
            sources: Sequence[str] | None = None,
            limit: int | None = 50
    ) -> list[VacancySchema]:
        async with self._uow_factory() as uow:
            vacancies = await uow.vacancies.get_by_status(
                status=status, sources=sources, limit=limit
            )
            return [VacancySchema.model_validate(vacancy) for vacancy in vacancies]

    async def save_details(self, *, vacancy_id: int, details: VacancyCreateSchema) -> None:
        """Fill a NEW vacancy with its collected details and mark it COLLECTED."""
        values: dict[str, t.Any] = {
            "title": details.title,
            "company": details.company,
            "description": details.description,
            "status": VacancyStatus.COLLECTED,
        }
        # keep the posted_at from the search if the details page has none
        if details.posted_at is not None:
            values["posted_at"] = details.posted_at

        async with self._uow_factory() as uow:
            await uow.vacancies.update_details(id=vacancy_id, values=values)
            await uow.commit()

    async def mark_failed(self, *, vacancy_id: int) -> None:
        async with self._uow_factory() as uow:
            await uow.vacancies.set_status(id=vacancy_id, status=VacancyStatus.FAILED)
            await uow.commit()
    ################################################################################
