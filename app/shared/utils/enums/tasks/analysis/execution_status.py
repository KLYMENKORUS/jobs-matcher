from enum import IntEnum


class AnalysisExecutionStatus(IntEnum):
    START = 1
    PREPARE_CVS = 2
    PREFILTER_VACANCIES = 3
    ANALYZE_VACANCIES = 4
    COMPLETED = 5
