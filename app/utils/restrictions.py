from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from ..models import EmployeeORM, ProjectORM, EmployeeProjectAssignmentORM


async def is_assignment_allowed(db: AsyncSession, employee: EmployeeORM, project: ProjectORM):
    """
    Проверяет, может ли сотрудник быть назначен на проект с учётом ранга и текущих назначений.
    """
    # Загружаем текущие назначения сотрудника с проектами
    result = await db.execute(
        select(EmployeeProjectAssignmentORM)
        .filter(EmployeeProjectAssignmentORM.employee_id == employee.id)
        .options(selectinload(EmployeeProjectAssignmentORM.project))
    )
    assignments = result.scalars().all()

    if not assignments:
        # Если назначений нет, любой проект разрешен
        return True, ""

    # Разделяем проекты на верхнеуровневые и подсчитываем подпроекты
    top_level_projects = {
        assignment.project for assignment in assignments if assignment.project.parent_id is None
    }
    subprojects_count = {
        project.id: sum(1 for assignment in assignments if assignment.project.parent_id == project.id)
        for project in top_level_projects
    }

    # Проверяем ограничения по рангу
    if employee.rank == "1":
        return True, ""  # Нет ограничений

    if employee.rank == "2":
        # До 3 верхнеуровневых проектов, подпроекты не ограничены
        is_valid = (
                len(top_level_projects) < 3 or await is_subproject_of_any(project, top_level_projects, db)
        )
        return is_valid, (
            "" if is_valid else "Ранг 2: нельзя участвовать более чем в 3 верхнеуровневых проектах"
        )

    if employee.rank == "3":
        # Проверяем лимит верхнеуровневых проектов
        if project.parent_id is None:
            is_valid = len(top_level_projects) < 2
            return is_valid, (
                "" if is_valid else "Ранг 3: нельзя участвовать более чем в 2 верхнеуровневых проектах"
            )

        for top_level_project in top_level_projects:
            if await is_subproject(project, top_level_project, db):
                is_valid = subprojects_count.get(top_level_project.id, 0) < 2
                return is_valid, (
                    "" if is_valid else "Ранг 3: нельзя участвовать более чем в 2 подпроектах одного верхнеуровневого проекта"
                )

        return False, "Ранг 3: подпроект не принадлежит верхнеуровневому проекту, в котором участвует сотрудник"

    if employee.rank == "4":
        # До 1 верхнеуровневого проекта и до 1 подпроекта
        if len(top_level_projects) >= 1:
            # Если есть верхнеуровневый проект, проверяем подпроект
            is_valid_subproject = await is_subproject_with_limit(project, top_level_projects, subprojects_count, 1, db)
            if is_valid_subproject:
                return True, ""
            else:
                return False, "Ранг 4: нельзя участвовать более чем в 1 верхнеуровневом проекте и 1 подпроекте"
        else:
            # Если верхнеуровневого проекта нет, проверяем, не является ли проект верхнеуровневым
            if project.parent_id is None:
                return True, ""
            else:
                return False, "Ранг 4: нельзя назначить проект без основного верхнеуровневого проекта"

    return False, "Неподдерживаемый ранг сотрудника"


async def is_subproject_with_limit(project, top_level_projects, subprojects_count, limit, db):
    """
    Проверяет, является ли проект подпроектом одного из верхнеуровневых проектов
    и не превышает ли ограничение на количество подпроектов.
    """
    for top_level_project in top_level_projects:
        if await is_subproject(project, top_level_project, db):
            return subprojects_count.get(top_level_project.id, 0) < limit
    return False


async def is_subproject(project, top_level_project, db):
    """
    Рекурсивно проверяет, является ли проект подпроектом верхнеуровневого проекта.
    """
    while project:
        if project.parent_id == top_level_project.id:
            return True
        result = await db.execute(select(ProjectORM).filter(ProjectORM.id == project.parent_id))
        project = result.scalar_one_or_none()
    return False


async def is_subproject_of_any(project: ProjectORM, top_level_projects: set, db: AsyncSession):
    results = [await is_subproject(project, top_level_project, db) for top_level_project in top_level_projects]
    return any(results)
