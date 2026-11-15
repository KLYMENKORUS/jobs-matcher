import datetime as dt

from app.modules.domains.users import UserSchema
from app.shared.settings import settings
from app.shared.utils.enums.tasks import ParsingExecutionStatus as ExecutionStatus
from app.shared.utils.logger.decorators import delimit_wrapper

from ..._base.states import BaseTaskState
from ..task import ParsingTask


class ParsingLinkVacanciesToUsersState(BaseTaskState):
    """
    Link COLLECTED vacancies to every active user whose keywords found them:
    one NEW `user_vacancy_interactions` row per (user, vacancy), which the
    analysis then scores.

    Idempotent (ON CONFLICT DO NOTHING on (user_id, vacancy_id)), a re-run only
    adds the links that are missing. Vacancies older than PARSING_LOOKBACK_DAYS
    are not linked, so a new user does not get the whole archive.
    """
    task: ParsingTask
    execution_status = ExecutionStatus.LINK_VACANCIES_TO_USERS

    @delimit_wrapper(
        section="parsing", obj="link-vacancies-to-users",
        detail="create new interactions", is_subdelimit=True
    )
    async def run(self) -> None:
        users: list[UserSchema] = await self.task.user_service.get_active_users()
        created_since: dt.datetime = (
            dt.datetime.now(dt.UTC) - dt.timedelta(days=settings.PARSING_LOOKBACK_DAYS)
        )

        linked: dict[str, int] = {}
        for user in users:
            keywords: list[str] = user.settings.keywords if user.settings else []
            if not keywords:
                continue

            count: int = await self.task.interaction_service.link_to_user(
                user_id=user.id, keywords=keywords, created_since=created_since
            )
            linked[str(user.id)] = count

            self.task.logger.info(
                f"[{self.task.log_labels}] user (id: {user.id}): linked {count} vacancies"
            )

        await self.task.merge_details(linked=linked)
