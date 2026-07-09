import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import settings
from app.db.base import Base

# Later, when we create models, we will import them here
# so Alembic can detect them during autogenerate.
#
# Example:
# from app.models.user import User
# from app.models.organization import Organization


config = context.config

# Use DATABASE_URL from app settings / .env
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Configure Python logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Alembic metadata target
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in offline mode.

    This does not need a live database connection.
    Alembic generates SQL statements using the configured URL.
    """
    url = settings.DATABASE_URL

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """
    Run migrations using an existing synchronous connection.

    Alembic itself works synchronously, so when we use SQLAlchemy async engine,
    we pass the sync connection through connection.run_sync(...).
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Create async engine and run migrations online.
    """
    section = config.get_section(config.config_ini_section)

    if section is None:
        raise RuntimeError("Alembic configuration section not found.")

    connectable = async_engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """
    Run migrations in online mode.
    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
