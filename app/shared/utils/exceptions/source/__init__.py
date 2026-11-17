__all__ = (
    "NotAVacancyUrlError",
    "SourceApiDataError",
    "SourceDataExtractionError",
    "SourceDataExtractorNotFoundError",
)

import abc

from app.shared.utils.logger import LogLabels

from .._base import BaseErrorException


class _BaseSourceErrorException(BaseErrorException, abc.ABC):
    def __init__(self) -> None:
        # ------------------------------------------------------------------------ #
        self.log_labels: LogLabels = LogLabels.SOURCE_API
        # ------------------------------------------------------------------------ #
        super().__init__()


class SourceDataExtractionError(_BaseSourceErrorException):
    def __init__(self, *, source: str, datatype: str) -> None:
        # ------------------------------------------------------------------------ #
        self.source, self.datatype = source, datatype
        # ------------------------------------------------------------------------ #
        super().__init__()

    def __str__(self) -> str:
        return f"[{self.log_labels}] {self.source} data extraction error ({self.datatype})"

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.source}, {self.datatype})"


class SourceApiDataError(_BaseSourceErrorException):
    """A source API answered, but its payload did not match the expected schema."""

    def __init__(self, *, source: str, api: str, path: str) -> None:
        # ------------------------------------------------------------------------ #
        self.source: str = source
        # ------------------------------------------------------------------------ #
        self.api: str = api
        # ------------------------------------------------------------------------ #
        self.path: str = path
        # ------------------------------------------------------------------------ #
        super().__init__()

    def __str__(self) -> str:
        return (
            f"[{self.log_labels}]  {self.source} api response data validation error "
            f"({self.api} / {self.path})"
        )

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.source!r}, {self.api!r}, {self.path!r})"


class NotAVacancyUrlError(_BaseSourceErrorException):
    """The URL does not point to a single vacancy page of the source."""

    def __init__(self, *, url: str, source: str) -> None:
        # ------------------------------------------------------------------------ #
        self.url: str = url
        # ------------------------------------------------------------------------ #
        self.source: str = source
        # ------------------------------------------------------------------------ #
        super().__init__()

    def __str__(self) -> str:
        return (
            f"[{self.log_labels}] {self.source} url is not a vacancy url: {self.url}"
        )

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.url!r}, {self.source!r})"


class SourceDataExtractorNotFoundError(_BaseSourceErrorException):
    """No data extractor is registered for the source."""

    def __init__(self, *, source: str) -> None:
        # ------------------------------------------------------------------------ #
        self.source: str = source
        # ------------------------------------------------------------------------ #
        super().__init__()

    def __str__(self) -> str:
        return (
            f"[{self.log_labels}] data extractor not found for source: {self.source}"
        )

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.source!r})"
