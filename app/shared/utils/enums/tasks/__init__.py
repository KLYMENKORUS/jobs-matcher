__all__ = (
    "TaskType",
    "ParsingExecutionStatus",
    "AnalysisExecutionStatus",
    "SendingExecutionStatus",
)

from enum import StrEnum

from .analysis import AnalysisExecutionStatus
from .parsing import ParsingExecutionStatus
from .sending import SendingExecutionStatus


class TaskType(StrEnum):
    PARSING = "parsing"
    ANALYSIS = "analysis"
    SENDING = "sending"
