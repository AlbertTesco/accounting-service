from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app import database, models
from app.database import get_db
from app.models import ProjectORM, EmployeeORM, EmployeeProjectAssignmentORM
from app.schemas.assignment import EmployeeProjectAssignmentCreate, EmployeeProjectAssignmentDelete, \
    EmployeeProjectAssignmentByRank
from app.utils.restrictions import is_assignment_allowed

router = APIRouter()


@router.post("/add-employee-to-project")
async def add_employee_to_project(data: EmployeeProjectAssignmentCreate, db: AsyncSession = Depends(get_db)):
    # Проверка существования проекта
    query = (
        select(ProjectORM)
        .filter(ProjectORM.id == data.project_id)
    )
    result = await db.execute(query)
    db_project = result.scalar_one_or_none()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Проверка существования сотрудника
    query = (
        select(EmployeeORM)
        .filter(EmployeeORM.id == data.employee_id)
    )
    result = await db.execute(query)
    db_employee = result.scalar_one_or_none()
    if not db_employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Проверка на существующее назначение
    query = (
        select(models.EmployeeProjectAssignmentORM)
        .filter(models.EmployeeProjectAssignmentORM.project_id == data.project_id,
                models.EmployeeProjectAssignmentORM.employee_id == data.employee_id)
    )
    result = await db.execute(query)
    existing_assignment = result.scalar_one_or_none()

    if existing_assignment:
        raise HTTPException(status_code=400, detail="EmployeeORM already assigned to this project")

    # Проверка ограничений на назначение с помощью is_assignment_allowed
    if not data.ignore_conflicts:
        is_allowed, conflict_reason = await is_assignment_allowed(db=db, employee=db_employee, project=db_project)
        if not is_allowed:
            raise HTTPException(status_code=400, detail=conflict_reason)

    # Создание нового назначения
    new_assignment = models.EmployeeProjectAssignmentORM(employee_id=data.employee_id, project_id=data.project_id)

    db.add(new_assignment)
    await db.commit()

    return {"message": "Employee added to project successfully"}


@router.delete("/delete-employee-to-project")
async def remove_employee_from_project(data: EmployeeProjectAssignmentDelete,
                                       db: AsyncSession = Depends(database.get_db)):
    # Проверка существования проекта
    query = (
        select(ProjectORM)
        .filter(ProjectORM.id == data.project_id)
    )
    result = await db.execute(query)
    db_project = result.scalar_one_or_none()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Проверка существования сотрудника
    query = (
        select(EmployeeORM)
        .filter(EmployeeORM.id == data.employee_id)
    )
    result = await db.execute(query)
    db_employee = result.scalar_one_or_none()

    if not db_employee:
        raise HTTPException(status_code=404, detail="EmployeeORM not found")

    query = (
        select(EmployeeProjectAssignmentORM)
        .filter(EmployeeProjectAssignmentORM.project_id == data.project_id,
                EmployeeProjectAssignmentORM.employee_id == data.employee_id)
    )

    result = await db.execute(query)
    existing_assignment = result.scalar_one_or_none()

    if not existing_assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    await db.delete(existing_assignment)
    await db.commit()
    return {"message": "Employee removed from project successfully"}


@router.post("/assign-employees-by-rank/")
async def assign_employees_by_rank(
        assignment_data: EmployeeProjectAssignmentByRank,
        db: AsyncSession = Depends(get_db),
):
    """
    Эндпоинт для назначения сотрудников определённого ранга в проект.
    Если ignore_conflicts=True, все сотрудники добавляются в проект, независимо от конфликтов.
    Если ignore_conflicts=False, сотрудники с конфликтами не добавляются.
    """
    # Получаем проект по ID
    result = await db.execute(select(ProjectORM).filter(ProjectORM.id == assignment_data.project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Получаем сотрудников с указанным рангом
    result = await db.execute(select(EmployeeORM).filter(EmployeeORM.rank == assignment_data.rank))
    employees = result.scalars().all()

    if not employees:
        raise HTTPException(status_code=404, detail=f"No employees with rank {assignment_data.rank} found")

    skipped_employees = []
    for employee in employees:
        is_allowed, conflict_details = await is_assignment_allowed(db, employee, project)

        if not is_allowed and not assignment_data.ignore_conflicts:
            # Добавляем информацию о сотрудниках, не прошедших проверку
            skipped_employees.append({
                "employee_id": employee.id,
                "name": employee.name,
                "conflict_details": conflict_details,
            })
            continue

        # Добавляем сотрудника в проект
        new_assignment = EmployeeProjectAssignmentORM(
            employee_id=employee.id,
            project_id=project.id,
        )
        db.add(new_assignment)

    # Сохраняем изменения
    await db.commit()

    # Возвращаем результат
    return {
        "message": f"Employees with rank {assignment_data.rank} processed for project {assignment_data.project_id}",
        "skipped_employees": skipped_employees,
    }
