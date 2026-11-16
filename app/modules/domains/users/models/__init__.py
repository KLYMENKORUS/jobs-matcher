__all__ = ("User",)

import typing as t
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base

if t.TYPE_CHECKING:
    from app.modules.domains.interactions.models import UserVacancyInteraction
    from app.modules.domains.user_settings.models import UserSettings


class User(Base):
    __tablename__ = "users"

    # [columns]
    ################################################################################
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    # path to the uploaded CV file (pdf / docx / txt) under settings.CV_STORAGE_DIR
    cv_file: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    ################################################################################

    # [relationships]
    ################################################################################
    settings: Mapped[UserSettings] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    interactions: Mapped[list[UserVacancyInteraction]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    ################################################################################
