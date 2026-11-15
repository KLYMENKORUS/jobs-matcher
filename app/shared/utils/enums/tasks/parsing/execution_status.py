from enum import IntEnum


class ParsingExecutionStatus(IntEnum):
    START = 1
    PREPARE_SEARCH_QUERIES = 2
    COLLECT_VACANCY_URLS = 3
    COLLECT_VACANCY_DETAILS = 4
    LINK_VACANCIES_TO_USERS = 5
    COMPLETED = 6
