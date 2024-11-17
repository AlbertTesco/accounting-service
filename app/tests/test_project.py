import tempfile

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker

from app.database import get_db
from app.main import app
from app.models import ProjectORM, Base


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


# Тестируем создание проекта
@pytest.mark.asyncio
async def test_create_project(client: AsyncClient, db_session: AsyncSession):
    project_data = {
        "name": "Test Project",
        "parent_id": None  # если родительский проект отсутствует
    }

    response = await client.post("/projects/", json=project_data)
    assert response.status_code == 200
    project = response.json()

    assert project["name"] == project_data["name"]
    assert project["parent_id"] == project_data["parent_id"]

    result = await db_session.execute(select(ProjectORM).filter_by(id=project["id"]))
    db_project = result.scalar_one_or_none()
    assert db_project is not None
    assert db_project.name == project_data["name"]
    assert db_project.parent_id == project_data["parent_id"]


@pytest.mark.asyncio
async def test_get_project_with_parent(client: AsyncClient, db_session: AsyncSession):
    # Создаем родительский проект
    parent_project = ProjectORM(name="Parent Project", parent_id=None)
    db_session.add(parent_project)
    await db_session.commit()

    project = ProjectORM(name="Test Project", parent_id=parent_project.id)
    db_session.add(project)
    await db_session.commit()

    response = await client.get(f"/projects/{project.id}")

    assert response.status_code == 200

    data = response.json()
    assert data["id"] == project.id
    assert data["name"] == project.name
    assert data["parent_id"] == parent_project.id
    assert data["parent_project"]["id"] == parent_project.id
    assert data["parent_project"]["name"] == parent_project.name


# Тестируем получение проекта с дочерними проектами
@pytest.mark.asyncio
async def test_get_project_with_subprojects(client: AsyncClient, db_session: AsyncSession):
    parent_project = ProjectORM(name="Parent Project", parent_id=None)
    db_session.add(parent_project)
    await db_session.commit()

    subproject = ProjectORM(name="Subproject", parent_id=parent_project.id)
    db_session.add(subproject)
    await db_session.commit()

    await db_session.commit()

    response = await client.get(f"/projects/{parent_project.id}")

    # Проверяем статус ответа
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == parent_project.id
    assert data["name"] == parent_project.name
    assert data["subprojects"]
    assert len(data["subprojects"]) == 1
    assert data["subprojects"][0]["id"] == subproject.id
    assert data["subprojects"][0]["name"] == subproject.name


# Тестируем ошибку 404, если проект не найден
@pytest.mark.asyncio
async def test_get_project_not_found(client: AsyncClient):
    response = await client.get("/projects/9999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Project not found"}


@pytest.mark.asyncio
async def test_get_all_projects_with_subprojects(client: AsyncClient, db_session: AsyncSession):
    parent_project = ProjectORM(name="Parent Project", parent_id=None)
    db_session.add(parent_project)
    await db_session.commit()

    subproject = ProjectORM(name="Subproject", parent_id=parent_project.id)
    db_session.add(subproject)
    await db_session.commit()

    response = await client.get("/projects/")

    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    parent_project_out = data[0]
    assert parent_project_out["id"] == parent_project.id
    assert parent_project_out["name"] == parent_project.name
    assert len(parent_project_out["subprojects"]) == 1
    assert parent_project_out["subprojects"][0]["id"] == subproject.id
    assert parent_project_out["subprojects"][0]["name"] == subproject.name


# Тестируем получение всех проектов без дочерних проектов
@pytest.mark.asyncio
async def test_get_all_projects_without_subprojects(client: AsyncClient, db_session: AsyncSession):
    parent_project = ProjectORM(name="Parent Project", parent_id=None)
    db_session.add(parent_project)
    await db_session.commit()

    response = await client.get("/projects/")

    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    parent_project_out = data[0]
    assert parent_project_out["id"] == parent_project.id
    assert parent_project_out["name"] == parent_project.name
    assert parent_project_out["subprojects"] == []  # Дочерних проектов нет


# Тестируем, когда нет проектов в базе данных
@pytest.mark.asyncio
async def test_get_all_projects_no_projects(client: AsyncClient):
    response = await client.get("/projects/")

    assert response.status_code == 404
    assert response.json() == {"detail": "No projects found"}


@pytest.mark.asyncio
async def test_delete_project(client: AsyncClient, db_session: AsyncSession):
    # Создаем проект для теста
    project = ProjectORM(name="Test Project", parent_id=None)
    db_session.add(project)
    await db_session.commit()

    # Проверяем, что проект добавлен в базу данных
    result = await db_session.execute(select(ProjectORM).filter_by(id=project.id))
    db_project = result.scalar_one_or_none()
    assert db_project is not None

    # Отправляем запрос на удаление проекта
    response = await client.delete(f"/projects/{project.id}")

    # Проверяем, что проект был удален
    assert response.status_code == 200
    assert response.json() == {"message": "Project deleted successfully"}

    # Проверяем, что проект действительно удален
    result = await db_session.execute(select(ProjectORM).filter_by(id=project.id))
    db_project = result.scalar_one_or_none()
    assert db_project is None


@pytest.mark.asyncio
async def test_delete_project_not_found(client: AsyncClient):
    # Пытаемся удалить несуществующий проект
    response = await client.delete(f"/projects/{9999}")
    assert response.status_code == 404
    assert response.json() == {"detail": "Project not found"}
