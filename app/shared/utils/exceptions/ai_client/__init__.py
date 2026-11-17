__all__ = ("AIRunFailedException",)

from .._base import BaseErrorException


class AIRunFailedException(BaseErrorException):
    def __init__(self, *, client_type: str, reason: str) -> None:
        # ------------------------------------------------------------------------ #
        self.client_type: str = client_type
        # ------------------------------------------------------------------------ #
        self.reason: str = reason
        # ------------------------------------------------------------------------ #
        super().__init__()

    def __str__(self) -> str:
        return f"AI run failed for client '{self.client_type}': {self.reason}"

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.client_type!r}, {self.reason!r})"
