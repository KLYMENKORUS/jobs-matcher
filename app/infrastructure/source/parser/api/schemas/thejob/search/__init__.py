__all__ = (
    "JobSearch",
    "JobSearchPagination",
)

from pydantic import BaseModel, ConfigDict, Field

from ..job import Job


class JobSearchPagination(BaseModel):
    current: int = Field(default=1)
    previous: int | None = Field(default=None)
    next: int | None = Field(default=None)
    per_page: int = Field(default=20)
    pages: int = Field(default=0)
    count: int = Field(default=0)

    @property
    def has_next(self) -> bool:
        return self.next is not None


class JobSearch(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    jobs: list[Job] = Field(default_factory=list, alias="data")
    pagination: JobSearchPagination = Field(default_factory=JobSearchPagination)
