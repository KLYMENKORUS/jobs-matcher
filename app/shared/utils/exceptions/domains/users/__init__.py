__all__ = (
    "CVParsingError",
    "UnsupportedCVFormatError",
    "UserNotFoundError",
)

from pathlib import Path

from ..._base import BaseErrorException


class UnsupportedCVFormatError(BaseErrorException):
    def __init__(self, *, filename: str, supported: tuple[str, ...]) -> None:
        # ------------------------------------------------------------------------ #
        self.filename: str = filename
        # ------------------------------------------------------------------------ #
        self.supported: tuple[str, ...] = supported
        # ------------------------------------------------------------------------ #
        super().__init__()

    def __str__(self) -> str:
        return (
            f"unsupported cv format: filename={self.filename}, "
            f"supported={', '.join(self.supported)}"
        )

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.filename})"


class CVParsingError(BaseErrorException):
    def __init__(self, *, path: Path, reason: str) -> None:
        # ------------------------------------------------------------------------ #
        self.path: Path = path
        # ------------------------------------------------------------------------ #
        self.reason: str = reason
        # ------------------------------------------------------------------------ #
        super().__init__()

    def __str__(self) -> str:
        return f"cv parsing failed: path={self.path}, reason={self.reason}"

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.path})"


class UserNotFoundError(BaseErrorException):
    def __init__(
        self, *, telegram_id: int | None = None, user_id: int | None = None
    ) -> None:
        # ------------------------------------------------------------------------ #
        self.telegram_id: int | None = telegram_id
        # ------------------------------------------------------------------------ #
        self.user_id: int | None = user_id
        # ------------------------------------------------------------------------ #
        super().__init__()

    def __str__(self) -> str:
        return (
            f"user not found: telegram_id={self.telegram_id}, user_id={self.user_id}"
        )

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.telegram_id}, {self.user_id})"
