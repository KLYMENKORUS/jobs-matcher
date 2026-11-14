__all__ = ("UserSettings",)

import typing as t

from sqlalchemy import JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base

if t.TYPE_CHECKING:
    from app.modules.domains.users.models import User


class UserSettings(Base):
    __tablename__ = "user_settings"

    # [columns]
    ################################################################################
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    keywords: Mapped[list[str]] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(default=True)
    ################################################################################

    # [relationships]
    ################################################################################
    user: Mapped[User] = relationship(back_populates="settings")
    ################################################################################
