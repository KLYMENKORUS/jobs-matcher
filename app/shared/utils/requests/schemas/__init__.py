__all__ = (
    "ScraperRequestParams",
    "ScraperResponse",
)

import typing as t
from enum import StrEnum
from http import HTTPMethod

from aiohttp import ClientTimeout
from pydantic import BaseModel, ConfigDict, Field


class ScraperRequestParams(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True
    )

    ################################################################################
    class ResponseFormat(StrEnum):
        JSON = "json"
        HTML = "html"
        REDIRECT = "redirect"
    ################################################################################

    url: str
    method: HTTPMethod = Field(default=HTTPMethod.GET)
    headers: dict[str, t.Any] = Field(default_factory=dict)
    params: dict[str, t.Any] = Field(default_factory=dict)
    data: dict[str, t.Any] = Field(default_factory=dict)
    json_body: dict[str, t.Any] = Field(
        default_factory=dict, alias="json", serialization_alias="json"
    )
    allow_redirects: bool = Field(default=True)
    timeout: ClientTimeout | float = Field(default=ClientTimeout(total=15))
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON)


class ScraperResponse(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )

    json_data: t.Any | None = Field(default=None)
    text: str | None = Field(default=None)
