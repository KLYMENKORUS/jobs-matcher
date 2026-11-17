from enum import IntEnum


class SendingExecutionStatus(IntEnum):
    START = 1
    SEND_MATCHES = 2
    COMPLETED = 3
