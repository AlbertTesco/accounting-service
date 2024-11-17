from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ProjectORM, EmployeeORM
from app.schemas.assignment import EmployeeProjectAssignmentCreate


async def test_is_assignment_allowed_rank_1(client: AsyncClient, db_session: AsyncSession):
    # Создаем проект
    project = ProjectORM(name="New Project", parent_id=None)
    db_session.add(project)
    await db_session.commit()

    # Создаем сотрудника с рангом "1"
    employee = EmployeeORM(name="John Doe", rank="1")
    db_session.add(employee)
    await db_session.commit()

    # Данные для добавления в проект
    assignment_data = EmployeeProjectAssignmentCreate(employee_id=employee.id, project_id=project.id,
                                                      ignore_conflicts=False)

    # Отправляем запрос на добавление сотрудника в проект
    response = await client.post("/add-employee-to-project", json=assignment_data.dict())

    # Проверяем, что запрос успешен
    assert response.status_code == 200
    assert response.json() == {"message": "Employee added to project successfully"}


async def test_is_assignment_allowed_rank_2_limit_3_top_level_projects(client: AsyncClient, db_session: AsyncSession):
    # Создаем 3 верхнеуровневых проекта
    project_1 = ProjectORM(name="Project 1", parent_id=None)
    project_2 = ProjectORM(name="Project 2", parent_id=None)
    project_3 = ProjectORM(name="Project 3", parent_id=None)
    project_4 = ProjectORM(name="Project 4", parent_id=None)
    db_session.add_all([project_1, project_2, project_3, project_4])
    await db_session.commit()

    # Создаем сотрудника с рангом "2"
    employee = EmployeeORM(name="John Doe", rank="2")
    db_session.add(employee)
    await db_session.commit()

    # Попытка добавить сотрудника на 3 верхнеуровневых проекта
    assignment_data_1 = EmployeeProjectAssignmentCreate(employee_id=employee.id, project_id=project_1.id,
                                                        ignore_conflicts=False)
    assignment_data_2 = EmployeeProjectAssignmentCreate(employee_id=employee.id, project_id=project_2.id,
                                                        ignore_conflicts=False)
    assignment_data_3 = EmployeeProjectAssignmentCreate(employee_id=employee.id, project_id=project_3.id,
                                                        ignore_conflicts=False)
    assignment_data_4 = EmployeeProjectAssignmentCreate(employee_id=employee.id, project_id=project_4.id,
                                                        ignore_conflicts=False)

    # Отправляем запросы на добавление сотрудника в проекты
    await client.post("/add-employee-to-project", json=assignment_data_1.model_dump())
    await client.post("/add-employee-to-project", json=assignment_data_2.model_dump())
    await client.post("/add-employee-to-project", json=assignment_data_3.model_dump())

    # Проверяем, что на 4-й проект сотрудник уже не может быть добавлен
    response = await client.post("/add-employee-to-project", json=assignment_data_4.model_dump())
    assert response.status_code == 400
    assert response.json() == {"detail": "Ранг 2: нельзя участвовать более чем в 3 верхнеуровневых проектах"}


async def test_is_assignment_allowed_rank_3_limit_2_subprojects(client: AsyncClient, db_session: AsyncSession):
    # Создаем верхнеуровневый проект
    top_level_project = ProjectORM(name="Top Level Project", parent_id=None)
    db_session.add(top_level_project)
    await db_session.commit()

    # Создаем подпроекты
    subproject_1 = ProjectORM(name="Subproject 1", parent_id=top_level_project.id)
    subproject_2 = ProjectORM(name="Subproject 2", parent_id=top_level_project.id)
    subproject_3 = ProjectORM(name="Subproject 3", parent_id=top_level_project.id)
    db_session.add_all([subproject_1, subproject_2, subproject_3])
    await db_session.commit()

    # Создаем сотрудника с рангом "3"
    employee = EmployeeORM(name="John Doe", rank="3")
    db_session.add(employee)
    await db_session.commit()

    # Добавляем сотрудника на два подпроекта
    assignment_data_1 = EmployeeProjectAssignmentCreate(employee_id=employee.id, project_id=subproject_1.id,
                                                        ignore_conflicts=False)
    assignment_data_2 = EmployeeProjectAssignmentCreate(employee_id=employee.id, project_id=subproject_2.id,
                                                        ignore_conflicts=False)

    await client.post("/add-employee-to-project", json=assignment_data_1.model_dump())
    await client.post("/add-employee-to-project", json=assignment_data_2.model_dump())

    # Проверяем, что на третий подпроект сотрудник не может быть добавлен
    assignment_data_3 = EmployeeProjectAssignmentCreate(employee_id=employee.id, project_id=subproject_3.id,
                                                        ignore_conflicts=False)
    response = await client.post("/add-employee-to-project", json=assignment_data_3.model_dump())
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Ранг 3: подпроект не принадлежит верхнеуровневому проекту, в котором участвует сотрудник"}


async def test_is_assignment_allowed_rank_3_with_existing_projects(client: AsyncClient, db_session: AsyncSession):
    # Создаем верхнеуровневый проект
    top_level_project = ProjectORM(name="Top Level Project", parent_id=None)
    db_session.add(top_level_project)
    await db_session.commit()

    # Создаем сотрудника с рангом "3", который уже участвует в 2 подпроектах
    employee = EmployeeORM(name="John Doe", rank="3")
    db_session.add(employee)
    await db_session.commit()

    # Создаем два подпроекта, на которые сотрудник уже назначен
    subproject_1 = ProjectORM(name="Subproject 1", parent_id=top_level_project.id)
    subproject_2 = ProjectORM(name="Subproject 2", parent_id=top_level_project.id)
    db_session.add_all([subproject_1, subproject_2])
    await db_session.commit()

    # Добавляем сотрудника на два подпроекта
    assignment_data_1 = EmployeeProjectAssignmentCreate(employee_id=employee.id, project_id=subproject_1.id,
                                                        ignore_conflicts=False)
    assignment_data_2 = EmployeeProjectAssignmentCreate(employee_id=employee.id, project_id=subproject_2.id,
                                                        ignore_conflicts=False)

    await client.post("/add-employee-to-project", json=assignment_data_1.dict())
    await client.post("/add-employee-to-project", json=assignment_data_2.dict())

    # Создаем третий подпроект
    subproject_3 = ProjectORM(name="Subproject 3", parent_id=top_level_project.id)
    db_session.add(subproject_3)
    await db_session.commit()

    # Попытка добавить сотрудника на третий подпроект
    assignment_data_3 = EmployeeProjectAssignmentCreate(employee_id=employee.id, project_id=subproject_3.id,
                                                        ignore_conflicts=False)
    response = await client.post("/add-employee-to-project", json=assignment_data_3.dict())
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Ранг 3: подпроект не принадлежит верхнеуровневому проекту, в котором участвует сотрудник"}


async def test_is_assignment_allowed_rank_4(client: AsyncClient, db_session: AsyncSession):
    # Создаем верхнеуровневый проект
    top_level_project = ProjectORM(name="Top Level Project", parent_id=None)
    db_session.add(top_level_project)
    await db_session.commit()

    # Создаем подпроект
    subproject = ProjectORM(name="Subproject", parent_id=top_level_project.id)
    db_session.add(subproject)
    await db_session.commit()

    # Создаем сотрудника с рангом "4"
    employee = EmployeeORM(name="John Doe", rank="4")
    db_session.add(employee)
    await db_session.commit()

    # Попытка добавить сотрудника на верхнеуровневый проект и подпроект
    assignment_data_1 = EmployeeProjectAssignmentCreate(employee_id=employee.id, project_id=top_level_project.id,
                                                        ignore_conflicts=False)
    assignment_data_2 = EmployeeProjectAssignmentCreate(employee_id=employee.id, project_id=subproject.id,
                                                        ignore_conflicts=False)

    await client.post("/add-employee-to-project", json=assignment_data_1.dict())
    response = await client.post("/add-employee-to-project", json=assignment_data_2.dict())
    assert response.status_code == 200

    # Попытка добавить сотрудника на второй верхнеуровневый проект
    another_top_level_project = ProjectORM(name="Another Top Level Project", parent_id=None)
    db_session.add(another_top_level_project)
    await db_session.commit()

    assignment_data_3 = EmployeeProjectAssignmentCreate(employee_id=employee.id,
                                                        project_id=another_top_level_project.id, ignore_conflicts=False)
    response = await client.post("/add-employee-to-project", json=assignment_data_3.dict())
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Ранг 4: нельзя участвовать более чем в 1 верхнеуровневом проекте и 1 подпроекте"}
