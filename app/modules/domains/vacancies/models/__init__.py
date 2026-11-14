__all__ = (
    "Vacancy",
    "UserVacancyInteraction"
)

import typing as t
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base
from app.modules.domains.vacancies.enums import InteractionStatus

if t.TYPE_CHECKING:
    from app.modules.domains.users.models import User


class Vacancy(Base):
    __tablename__ = "vacancies"

    # [columns]
    ################################################################################
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255))
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(String(512), unique=True)
    source: Mapped[str] = mapped_column(String(50), index=True)
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
    ################################################################################


class UserVacancyInteraction(Base):
    __tablename__ = "user_vacancy_interactions"
    __table_args__ = (
        UniqueConstraint("user_id", "vacancy_id", name="uq_user_vacancy"),
    )

    # [columns]
    ################################################################################
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    vacancy_id: Mapped[int] = mapped_column(ForeignKey("vacancies.id", ondelete="CASCADE"))

    match_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    match_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[InteractionStatus] = mapped_column(
        Enum(
            InteractionStatus,
            name="interaction_status",
            values_callable=lambda enum: [member.value for member in enum],
        ),
        default=InteractionStatus.PENDING,
        index=True,
    )
    ################################################################################

    # [relationships]
    ################################################################################
    user: Mapped[User] = relationship(back_populates="interactions")
    vacancy: Mapped[Vacancy] = relationship(back_populates="interactions", lazy="selectin")
    ################################################################################
