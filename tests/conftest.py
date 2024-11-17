import tempfile

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.database import get_db
from app.main import app
from app.models import Base


@pytest.fixture(scope="function")
async def db_session():
    temp_dir = tempfile.TemporaryDirectory()
    DATABASE_URL = f"sqlite+aiosqlite:///{temp_dir.name}/test.db"
    engine = create_async_engine(DATABASE_URL, echo=True, future=True)

    # Создаем сессию для работы с базой данных
    SessionFactory = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with engine.begin() as conn:
        # Создаем все таблицы перед каждым тестом
        await conn.run_sync(Base.metadata.create_all)

    async_session = SessionFactory()
    try:
        # Возвращаем сессию для теста
        yield async_session
    finally:
        await async_session.rollback()
        await async_session.close()
        temp_dir.cleanup()


# Фикстура для тестового клиента
@pytest.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://127.0.0.1:8000/api") as ac:
        yield ac

    app.dependency_overrides.clear()
