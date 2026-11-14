__all__ = (
    "InteractionStatus",
    "VacancySource"
)

from enum import StrEnum


class InteractionStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    APPLIED = "applied"
    SKIPPED = "skipped"
    IGNORED = "ignored"


class VacancySource(StrEnum):
    DOU = "dou"
    DJINNI = "djinni"
    THE_JOB = "the-job"
    JOBICO = "jobico"
