__all__ = (
    "Job",
    "JobLocation",
)

import datetime as dt
import typing as t

from lxml.html import fromstring
from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel


class _TheJobModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="ignore",
    )


class JobLocation(_TheJobModel):
    country_name: str | None = Field(default=None)
    city_name: str | None = Field(default=None)
    work_mode: str | None = Field(default=None)


class Job(_TheJobModel):
    id: str
    title: str
    slug: str
    summary: str | None = Field(default=None)
    description: str = Field(default_factory=str)

    company_id: str | None = Field(default=None)
    company_name: str | None = Field(default=None)

    salary_min: float | None = Field(default=None)
    salary_currency: str | None = Field(default=None)
    salary_period: str | None = Field(default=None)
    salary_min_converted: float | None = Field(default=None)

    experience_levels: list[str] = Field(default_factory=list)
    employment_types: list[str] = Field(default_factory=list)
    tech_stack: list[str] = Field(default_factory=list)

    country_name: str | None = Field(default=None)
    locations: list[JobLocation] = Field(default_factory=list)

    is_active: bool = Field(default=True)
    archived: bool = Field(default=False)
    created_at: dt.datetime | None = Field(default=None)
    updated_at: dt.datetime | None = Field(default=None)
    source_posted_at: dt.datetime | None = Field(default=None)

    @model_validator(mode="before")
    @classmethod
    def prepare_data(cls, values: t.Any) -> t.Any:
        # ------------------------------------------------------------------------ #
        def _pick_language(*, translations: dict[str, t.Any]) -> str:
            # the API returns {"en": html, "ua": html, "ru": html}
            for lang in ("en", "ua", "ru"):
                if translations.get(lang):
                    return str(translations[lang])
            return str(next(iter(translations.values()), "") or "")

        def _html_to_text(*, html: str) -> str:
            if not html.strip():
                return ""
            text: str = fromstring(html).text_content()
            return "\n".join(line.strip() for line in text.splitlines() if line.strip())
        # ------------------------------------------------------------------------ #

        # ------------------------------------------------------------------------ #
        if not isinstance(values, dict):
            return values

        description: t.Any = values.get("descriptions") or values.get("description")

        if isinstance(description, dict):
            description = _pick_language(translations=description)
        # ------------------------------------------------------------------------ #

        return {
            **values,
            "description": _html_to_text(html=description) if isinstance(description, str) else "",
        }

    @property
    def is_remote(self) -> bool:
        return any(location.work_mode == "Remote" for location in self.locations)
