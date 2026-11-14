__all__ = (
    "BaseErrorException",
)

import abc

from app.shared.utils.logger import logger


class BaseErrorException(Exception, abc.ABC):

    def __init__(self) -> None:
        super().__init__(str(self))

        # ------------------------------------------------------------------------ #
        logger.error(str(self))
        # ------------------------------------------------------------------------ #

    @abc.abstractmethod
    def __str__(self) -> str:
        pass

    @abc.abstractmethod
    def __repr__(self) -> str:
        pass