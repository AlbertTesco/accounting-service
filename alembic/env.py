import os
from logging.config import fileConfig

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy import pool
from alembic import context

from app.models import Base  # Импорт моделей базы данных

# Загрузка переменных окружения из .env
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Конфигурация alembic
config = context.config

# Настройка логирования
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Метаданные базы данных
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Запуск миграций в режиме 'offline'.

    В этом случае URL передается напрямую, движок не создается.
    """
    # Передаем URL базы данных из переменной окружения
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Запуск миграций в режиме 'online'."""
    # Создаем движок с URL базы данных из переменной окружения
    connectable = create_async_engine(
        DATABASE_URL,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        def do_run_migrations(sync_connection):
            context.configure(
                connection=sync_connection,
                target_metadata=target_metadata,
                render_as_batch=True,
            )
            with context.begin_transaction():
                context.run_migrations()

        await connection.run_sync(do_run_migrations)


if context.is_offline_mode():
    run_migrations_offline()
else:
    import asyncio

    asyncio.run(run_migrations_online())
