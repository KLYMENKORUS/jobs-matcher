__all__ = ("UserService",)

import asyncio
import typing as t
from pathlib import Path

from app.infrastructure.database.service import UnitOfWork
from app.modules.cv_parser import CVParser
from app.modules.domains.users.models import User
from app.modules.domains.users.schemas import UserCreateSchema, UserSchema
from app.shared.settings import settings
from app.shared.utils.exceptions.domains.users import UserNotFoundError
from app.shared.utils.logger.decorators import delimit_wrapper


class UserService:

    def __init__(self, *, uow_factory: t.Callable[[], UnitOfWork] = UnitOfWork) -> None:
        # ------------------------------------------------------------------------ #
        self._uow_factory: t.Callable[[], UnitOfWork] = uow_factory
        # ------------------------------------------------------------------------ #

    @staticmethod
    async def _get_user_or_raise(uow: UnitOfWork, *, telegram_id: int) -> User:
        user: User | None = await uow.users.get_by_telegram_id(telegram_id=telegram_id)
        if user is None:
            raise UserNotFoundError(telegram_id=telegram_id)
        return user

    # [read]
    ################################################################################
    async def get_by_telegram_id(self, *, telegram_id: int) -> UserSchema | None:
        async with self._uow_factory() as uow:
            user: User | None = await uow.users.get_by_telegram_id(telegram_id=telegram_id)
            return UserSchema.model_validate(user) if user else None

    async def get_active_users(self) -> list[UserSchema]:
        async with self._uow_factory() as uow:
            users = await uow.users.get_active()
            return [UserSchema.model_validate(user) for user in users]
    ################################################################################

    # [write]
    ################################################################################
    @delimit_wrapper(section="users", obj="service", detail="register", is_subdelimit=True)
    async def register(self, *, data: UserCreateSchema) -> UserSchema:
        async with self._uow_factory() as uow:
            # ------------------------------------------------------------------------ #
            user: User | None = await uow.users.get_by_telegram_id(
                telegram_id=data.telegram_id
            )
            if user is not None:
                return UserSchema.model_validate(user)
            # ------------------------------------------------------------------------ #

            # ------------------------------------------------------------------------ #
            user = await uow.users.create_with_settings(
                telegram_id=data.telegram_id, keywords=data.keywords
            )
            await uow.commit()
            # ------------------------------------------------------------------------ #

            return UserSchema.model_validate(user)

    async def update_cv(self, *, telegram_id: int, filename: str, content: bytes) -> UserSchema:
        """
        Saves the uploaded CV as `<CV_STORAGE_DIR>/<telegram_id><ext>` and stores
        its path; the text is extracted later, by the analysis.
        """
        extension: str = CVParser.ensure_supported(filename=filename)

        async with self._uow_factory() as uow:
            # ------------------------------------------------------------------------ #
            user: User = await self._get_user_or_raise(uow, telegram_id=telegram_id)
            old_path: Path | None = Path(user.cv_file) if user.cv_file else None
            new_path: Path = settings.CV_STORAGE_DIR / f"{telegram_id}{extension}"
            # ------------------------------------------------------------------------ #

            # ------------------------------------------------------------------------ #
            await asyncio.to_thread(self._write_file, new_path, content)
            user.cv_file = str(new_path)
            await uow.commit()
            result: UserSchema = UserSchema.model_validate(user)
            # ------------------------------------------------------------------------ #

        # a CV re-uploaded in another format leaves the old file behind
        if old_path is not None and old_path != new_path:
            old_path.unlink(missing_ok=True)

        return result

    async def delete(self, *, telegram_id: int) -> None:
        async with self._uow_factory() as uow:
            user: User = await self._get_user_or_raise(uow, telegram_id=telegram_id)
            cv_file: str | None = user.cv_file
            await uow.session.delete(user)
            await uow.commit()

        if cv_file:
            Path(cv_file).unlink(missing_ok=True)
    ################################################################################

    @staticmethod
    def _write_file(path: Path, content: bytes) -> None:
        # write to a temp file and rename, so a worker never reads a half-written CV
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path: Path = path.with_name(f"{path.name}.tmp")
        tmp_path.write_bytes(content)
        tmp_path.replace(path)
