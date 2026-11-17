__all__ = ("InteractionCallback",)

import typing as t

from pydantic import BaseModel, ValidationError

from app.shared.utils.enums.domains.interactions import InteractionStatus


class InteractionCallback(BaseModel):
    """
    The user's reaction to a sent vacancy: the inline buttons under the message
    carry it as `callback_data` ("ia:<interaction id>:<status>", telegram
    allows 64 bytes), the bot unpacks it and calls InteractionService.react.
    """
    PREFIX: t.ClassVar[str] = "ia"
    REACTIONS: t.ClassVar[dict[InteractionStatus, str]] = {
        InteractionStatus.APPLIED: "✅ Подався",
        InteractionStatus.SKIPPED: "🙈 Пропустити",
    }

    interaction_id: int
    status: InteractionStatus

    def pack(self) -> str:
        return f"{self.PREFIX}:{self.interaction_id}:{self.status}"

    @classmethod
    def unpack(cls, data: str) -> InteractionCallback | None:
        """None for foreign or broken data."""
        prefix, _, rest = data.partition(":")
        interaction_id, _, status = rest.partition(":")
        if prefix != cls.PREFIX:
            return None

        try:
            callback = cls(interaction_id=interaction_id, status=status)  # type: ignore[arg-type]
        except ValidationError:
            return None

        return callback if callback.status in cls.REACTIONS else None

    @classmethod
    def keyboard(cls, *, interaction_id: int) -> dict[str, t.Any]:
        """`reply_markup` for the vacancy message."""
        return {
            "inline_keyboard": [[
                {
                    "text": text,
                    "callback_data": cls(interaction_id=interaction_id, status=status).pack(),
                }
                for status, text in cls.REACTIONS.items()
            ]]
        }
