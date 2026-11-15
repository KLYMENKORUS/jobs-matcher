__all__ = (
    "VacancySource",
    "InteractionStatus",
)

from enum import StrEnum


class VacancySource(StrEnum):
    DOU = "dou"
    DJINNI = "djinni"
    THE_JOB = "thejob"
    JOBICO = "jobico"


class InteractionStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    APPLIED = "applied"
    SKIPPED = "skipped"
    IGNORED = "ignored"
