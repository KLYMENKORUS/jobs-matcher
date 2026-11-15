__all__ = ("UserVacancyInteraction",)

import typing as t

from sqlalchemy import Enum, Float, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base
from app.shared.utils.enums.domains.interactions import InteractionStatus

if t.TYPE_CHECKING:
    from app.modules.domains.users.models import User
    from app.modules.domains.vacancies.models import Vacancy


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
