__all__ = (
    "Vacancy",
    "VacancyKeyword",
)

import typing as t
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base
from app.shared.utils.enums.domains.vacancies import VacancyStatus

if t.TYPE_CHECKING:
    from app.modules.domains.interactions.models import UserVacancyInteraction


class Vacancy(Base):
    __tablename__ = "vacancies"

    # [columns]
    ################################################################################
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # title / description are empty while the vacancy is NEW (only its url is known)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(String(512), unique=True)
    source: Mapped[str] = mapped_column(String(50), index=True)
    status: Mapped[VacancyStatus] = mapped_column(
        Enum(
            VacancyStatus,
            name="vacancy_status",
            values_callable=lambda enum: [member.value for member in enum],
        ),
        default=VacancyStatus.NEW,
        server_default=VacancyStatus.NEW.value,
        index=True,
    )
    # when the source published it; the newest one per (source, keyword) is
    # where the next search stops paging
    posted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    ################################################################################

    # [relationships]
    ################################################################################
    interactions: Mapped[list[UserVacancyInteraction]] = relationship(
        back_populates="vacancy",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    keywords: Mapped[list[VacancyKeyword]] = relationship(
        back_populates="vacancy",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    ################################################################################


class VacancyKeyword(Base):
    """Which search keyword a vacancy was found by (one vacancy - many keywords)."""

    __tablename__ = "vacancy_keywords"
    __table_args__ = (
        UniqueConstraint("vacancy_id", "keyword", name="uq_vacancy_keyword"),
    )

    # [columns]
    ################################################################################
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    vacancy_id: Mapped[int] = mapped_column(
        ForeignKey("vacancies.id", ondelete="CASCADE"), index=True
    )
    keyword: Mapped[str] = mapped_column(String(255), index=True)
    ################################################################################

    # [relationships]
    ################################################################################
    vacancy: Mapped[Vacancy] = relationship(back_populates="keywords")
    ################################################################################
