__all__ = (
    "VacancySource",
    "VacancyStatus",
)

from enum import StrEnum


class VacancySource(StrEnum):
    DOU = "dou"
    DJINNI = "djinni"
    THE_JOB = "thejob"
    JOBICO = "jobico"


class VacancyStatus(StrEnum):
    # url (and maybe posted_at) is known from the search, details not collected yet
    NEW = "new"
    # all fields are collected, the vacancy can be linked to users
    COLLECTED = "collected"
    # collecting the details failed, the vacancy is skipped
    FAILED = "failed"
