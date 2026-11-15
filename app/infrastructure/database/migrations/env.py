import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from app.infrastructure.database.base import Base

# [models]
# ------------------------------------------------------------------------------ #
# every model module must be imported here so its tables land in Base.metadata,
# otherwise autogenerate will think the table was removed and emit a DROP
from app.modules.domains.interactions import models as _interactions_models  # noqa: F401
from app.modules.domains.tasks.execution import models as _task_runs_models  # noqa: F401
from app.modules.domains.user_settings import models as _user_settings_models  # noqa: F401
from app.modules.domains.users import models as _users_models  # noqa: F401
from app.modules.domains.vacancies import models as _vacancies_models  # noqa: F401
from app.shared.settings import settings

# ------------------------------------------------------------------------------ #

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# the URL is taken from app settings (.env), not from alembic.ini, so credentials
# live in one place; passed straight to the engine to avoid configparser `%` issues
DATABASE_URL: str = str(settings.DATABASE_URL)


def run_migrations_offline() -> None:
    """Emit SQL to stdout instead of running it (`alembic upgrade head --sql`)."""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = create_async_engine(DATABASE_URL, poolclass=pool.NullPool)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
