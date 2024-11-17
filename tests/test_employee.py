from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models import EmployeeORM
from app.schemas.employee import EmployeeCreate


async def test_create_employee(client: AsyncClient, db_session: AsyncSession):
    employee_data = {
        "name": "Sensey",
        "rank": "1"
    }

    # Отправляем запрос на создание сотрудника с использованием json
    response = await client.post("/employees/", json=employee_data)

    # Проверяем статус ответа
    assert response.status_code == 200
    employee = response.json()

    # Проверяем данные сотрудника
    assert employee["name"] == employee_data["name"]
    assert employee["rank"] == employee_data["rank"]

    # Проверяем, что сотрудник был добавлен в базу данных
    result = await db_session.execute(select(EmployeeORM).filter_by(id=employee["id"]))
    db_employee = result.scalar_one_or_none()
    assert db_employee is not None
    assert db_employee.name == employee_data["name"]
    assert db_employee.rank == employee_data["rank"]


async def test_get_employees(client: AsyncClient, db_session: AsyncSession):
    # Создаем сотрудников для теста
    employee_1 = EmployeeCreate(name="John Doe", rank="1")
    employee_2 = EmployeeCreate(name="Jane Doe", rank="2")

    # Добавляем сотрудников в базу
    db_session.add(EmployeeORM(name=employee_1.name, rank=employee_1.rank))
    db_session.add(EmployeeORM(name=employee_2.name, rank=employee_2.rank))
    await db_session.commit()

    # Отправляем запрос на получение всех сотрудников
    response = await client.get("/employees/")

    # Проверяем статус ответа
    assert response.status_code == 200
    employees = response.json()

    # Проверяем, что два сотрудника были добавлены в базу данных
    assert len(employees) == 2
    assert employees[0]["name"] == "John Doe"
    assert employees[1]["name"] == "Jane Doe"


async def test_get_employee_by_id(client: AsyncClient, db_session: AsyncSession):
    # Создаем сотрудника для теста
    employee_data = {
        "name": "John Doe",
        "rank": "1"
    }

    employee = EmployeeORM(name=employee_data["name"], rank=employee_data["rank"])
    db_session.add(employee)
    await db_session.commit()

    # Отправляем запрос на получение сотрудника по ID
    response = await client.get(f"/employees/{employee.id}")

    # Проверяем статус ответа
    assert response.status_code == 200
    employee_from_response = response.json()

    # Проверяем данные сотрудника
    assert employee_from_response["name"] == employee_data["name"]
    assert employee_from_response["rank"] == employee_data["rank"]



async def test_update_employee(client: AsyncClient, db_session: AsyncSession):
    # Создаем сотрудника для теста
    employee_data = {
        "name": "John Doe",
        "rank": "2"
    }

    employee = EmployeeORM(name=employee_data["name"], rank=employee_data["rank"])
    db_session.add(employee)
    await db_session.commit()

    # Данные для обновления
    updated_data = {
        "name": "John Updated",
        "rank": "1"
    }

    # Отправляем запрос на обновление сотрудника
    response = await client.put(f"/employees/{employee.id}", json=updated_data)

    # Проверяем статус ответа
    assert response.status_code == 200
    updated_employee = response.json()

    # Проверяем, что данные были обновлены
    assert updated_employee["name"] == updated_data["name"]
    assert updated_employee["rank"] == updated_data["rank"]

    # Проверяем, что данные в базе тоже обновлены
    result = await db_session.execute(select(EmployeeORM).filter_by(id=employee.id))
    db_employee = result.scalar_one_or_none()
    assert db_employee.name == updated_data["name"]
    assert db_employee.rank == updated_data["rank"]



async def test_delete_employee(client: AsyncClient, db_session: AsyncSession):
    # Создаем сотрудника для теста
    employee_data = {
        "name": "John Doe",
        "rank": "1"
    }

    employee = EmployeeORM(name=employee_data["name"], rank=employee_data["rank"])
    db_session.add(employee)
    await db_session.commit()

    # Отправляем запрос на удаление сотрудника
    response = await client.delete(f"/employees/{employee.id}")

    # Проверяем статус ответа
    assert response.status_code == 200
    assert response.json() == {"message": "Employee deleted successfully"}

    # Проверяем, что сотрудник действительно удален из базы данных
    result = await db_session.execute(select(EmployeeORM).filter_by(id=employee.id))
    db_employee = result.scalar_one_or_none()
    assert db_employee is None
