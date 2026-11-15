__all__ = ("InteractionStatus",)

from enum import StrEnum


class InteractionStatus(StrEnum):
    # linked to the user by keyword, not analysed yet
    NEW = "new"
    # analysed, waiting to be sent (if the score passes the user's min_score)
    PENDING = "pending"
    SENT = "sent"
    APPLIED = "applied"
    SKIPPED = "skipped"
    IGNORED = "ignored"
