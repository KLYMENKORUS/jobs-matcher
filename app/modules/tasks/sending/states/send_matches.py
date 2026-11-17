import html

from app.clients.tg_client import TelegramApiNotifierClient
from app.modules.domains.interactions import InteractionWithVacancySchema
from app.modules.domains.users import UserSchema
from app.shared.settings import settings
from app.shared.utils.enums.domains.interactions import InteractionStatus
from app.shared.utils.enums.tasks import (
    SendingExecutionStatus as ExecutionStatus,
)
from app.shared.utils.logger.decorators import delimit_wrapper

from ..._base.states import BaseTaskState
from ..callbacks import InteractionCallback
from ..task import SendingTask


class SendingSendMatchesState(BaseTaskState):
    """
    For every active user: send each PENDING match with score >= the user's
    current min_score and mark it SENT right after Telegram accepted it.

    The threshold is applied here, not in the analysis, so a changed
    min_score works on the next run without re-analysing anything.

    The message carries "applied / skip" buttons (InteractionCallback); their
    presses come to the bot, which saves them via InteractionService.react.
    """

    task: SendingTask
    execution_status = ExecutionStatus.SEND_MATCHES

    # matches sent per user per run, the rest go on the next run
    MAX_MATCHES_PER_USER: int = 20

    @delimit_wrapper(
        section="sending",
        obj="send-matches",
        detail="send matches to telegram",
        is_subdelimit=True,
    )
    async def run(self) -> None:
        users: list[UserSchema] = await self.task.user_service.get_active_users()

        sent: int = 0
        failed: int = 0

        for user in users:
            user_sent, user_failed = await self._send_user_matches(user=user)
            sent += user_sent
            failed += user_failed

        await self.task.merge_details(sent=sent, failed=failed)
        self.task.logger.info(
            f"[{self.task.log_labels}] sent {sent}, failed {failed}"
        )

    async def _send_user_matches(self, *, user: UserSchema) -> tuple[int, int]:
        # ------------------------------------------------------------------------ #
        min_score: float = (
            user.settings.min_score if user.settings else settings.DEFAULT_MIN_SCORE
        )
        matches: list[
            InteractionWithVacancySchema
        ] = await self.task.interaction_service.get_matches_to_send(
            user_id=user.id,
            min_score=min_score,
            limit=self.MAX_MATCHES_PER_USER,
        )
        if not matches:
            return 0, 0
        # ------------------------------------------------------------------------ #

        tg_client = TelegramApiNotifierClient(
            logger=self.task.logger, channel_id=str(user.telegram_id)
        )

        sent: int = 0
        failed: int = 0

        for match in matches:
            message_id: int | None = await tg_client.send_message(
                text=self._format_message(match=match),
                reply_markup=InteractionCallback.keyboard(interaction_id=match.id),
            )
            # send_message swallows HTTP errors and returns None: keep it PENDING
            if message_id is None:
                failed += 1
                self.task.logger.warning(
                    f"[{self.task.log_labels}] interaction (id: {match.id}) "
                    f"was not delivered to user (id: {user.id})"
                )
                continue

            await self.task.interaction_service.update_status(
                interaction_id=match.id, status=InteractionStatus.SENT
            )
            sent += 1

        return sent, failed

    @staticmethod
    def _format_message(*, match: InteractionWithVacancySchema) -> str:
        vacancy = match.vacancy
        company: str = (
            f" · {html.escape(vacancy.company)}" if vacancy.company else ""
        )

        return "\n".join(
            [
                f"<b>{html.escape(vacancy.title or 'Вакансія')}</b>{company}",
                f"🎯 Match: <b>{match.match_score or 0:.0f}/100</b>",
                "",
                html.escape(match.match_reasoning or ""),
                "",
                f'<a href="{html.escape(vacancy.url, quote=True)}">Відкрити вакансію</a>'
                f" ({html.escape(vacancy.source)})",
            ]
        )
