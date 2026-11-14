__all__ = (
    "InteractionNotFoundError",
)

from ..._base import BaseErrorException


class InteractionNotFoundError(BaseErrorException):

    def __init__(self, *, interaction_id: int) -> None:
        # ------------------------------------------------------------------------ #
        self.interaction_id: int = interaction_id
        # ------------------------------------------------------------------------ #
        super().__init__()

    def __str__(self) -> str:
        return f"interaction not found: id={self.interaction_id}"

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.interaction_id})"
