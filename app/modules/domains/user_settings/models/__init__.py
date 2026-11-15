__all__ = ("UserSettings",)

import typing as t

from sqlalchemy import JSON, CheckConstraint, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base
from app.shared.settings import settings

if t.TYPE_CHECKING:
    from app.modules.domains.users.models import User


class UserSettings(Base):
    __tablename__ = "user_settings"
    __table_args__ = (
        CheckConstraint("min_score >= 0 AND min_score <= 100", name="min_score_range"),
    )

    # [columns]
    ################################################################################
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    keywords: Mapped[list[str]] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(default=True)
    min_score: Mapped[float] = mapped_column(
        Float,
        default=settings.DEFAULT_MIN_SCORE,
        server_default=str(settings.DEFAULT_MIN_SCORE),
    )
    ################################################################################

    # [relationships]
    ################################################################################
    user: Mapped[User] = relationship(back_populates="settings")
    ################################################################################
