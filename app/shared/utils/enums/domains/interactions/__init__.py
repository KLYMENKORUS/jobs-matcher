__all__ = ("InteractionStatus",)

from enum import StrEnum


class InteractionStatus(StrEnum):
    NEW = "new"
    PENDING = "pending"
    SENT = "sent"
    APPLIED = "applied"
    SKIPPED = "skipped"
    IGNORED = "ignored"
