__all__ = ("InteractionStatus",)

from enum import StrEnum


class InteractionStatus(StrEnum):
    """
    NEW -> REJECTED                              (prefilter, no AI score)
    NEW -> PENDING -> SENT -> APPLIED | SKIPPED  (user's reaction in the bot)

    PENDING = scored by the AI; it is sent once score >= the user's current
    min_score, so lowering min_score needs no new analysis.
    """

    NEW = "new"
    REJECTED = "rejected"
    PENDING = "pending"
    SENT = "sent"
    APPLIED = "applied"
    SKIPPED = "skipped"
