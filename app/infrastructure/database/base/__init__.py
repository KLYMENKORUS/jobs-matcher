__all__ = ("Base",)

import typing as t

from sqlalchemy import MetaData, inspect
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):

    ################################################################################
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )
    ################################################################################

    def __repr__(self) -> str:
        primary_keys: dict[str, t.Any] = {
            column.name: getattr(self, column.name, None)
            for column in inspect(self.__class__).primary_key
        }
        values: str = ", ".join(f"{key}={value!r}" for key, value in primary_keys.items())
        return f"<{type(self).__name__}({values})>"
