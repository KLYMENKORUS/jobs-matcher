__all__ = (
    "UserNotFoundError",
)

from ..._base import BaseErrorException


class UserNotFoundError(BaseErrorException):

    def __init__(
            self, *,
            telegram_id: int | None = None,
            user_id: int | None = None
    ) -> None:
        # ------------------------------------------------------------------------ #
        self.telegram_id: int | None = telegram_id
        # ------------------------------------------------------------------------ #
        self.user_id: int | None = user_id
        # ------------------------------------------------------------------------ #
        super().__init__()

    def __str__(self) -> str:
        return (
            f"user not found: telegram_id={self.telegram_id}, "
            f"user_id={self.user_id}"
        )

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.telegram_id}, {self.user_id})"
