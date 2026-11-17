__all__ = ("HttpUrlStr",)

import typing as t

from pydantic import AfterValidator, AnyHttpUrl, TypeAdapter, ValidationError
from pydantic_core import PydanticCustomError

_HTTP_URL_ADAPTER: t.Final[TypeAdapter[AnyHttpUrl]] = TypeAdapter(AnyHttpUrl)


def _validate_http_url(value: str) -> str:
    try:
        return str(_HTTP_URL_ADAPTER.validate_python(value))
    except ValidationError:
        raise PydanticCustomError(
            "url_parsing", "Invalid format URL {value}", {"value": value}
        ) from None


HttpUrlStr = t.Annotated[str, AfterValidator(_validate_http_url)]
