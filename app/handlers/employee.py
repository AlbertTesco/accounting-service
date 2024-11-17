from typing import List

from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from .. import models, database
from ..database import get_db
from ..models import EmployeeProjectAssignmentORM, EmployeeORM
from ..schemas.employee import EmployeeCreate, EmployeeOut
from ..schemas.project import ProjectOut

router = APIRouter()


@router.post("/employees/", response_model=EmployeeOut)
async def create_employee(employee: EmployeeCreate, db: AsyncSession = Depends(get_db)):
    db_employee = models.EmployeeORM(name=employee.name, rank=employee.rank)
    db.add(db_employee)
    await db.commit()
    await db.refresh(db_employee)
    return EmployeeOut(id=db_employee.id, name=db_employee.name, rank=db_employee.rank, projects=[])


@router.get("/employees/", response_model=List[EmployeeOut])
async def get_employees(db: AsyncSession = Depends(database.get_db)):
    query = (
        select(EmployeeORM)
        .options(selectinload(EmployeeORM.projects).selectinload(EmployeeProjectAssignmentORM.project))
    )
    result = await db.execute(query)
    db_employee = result.scalars()

    if not db_employee:
        raise HTTPException(status_code=404, detail="Employees not found")

    return [
        EmployeeOut(
            id=employee.id,
            name=employee.name,
            rank=employee.rank,
            projects=[
                ProjectOut(id=assignment.project.id, name=assignment.project.name,
                           parent_id=assignment.project.parent_id)
                for assignment in employee.projects
            ],
        )
        for employee in db_employee
    ]


@router.get("/employees/{employee_id}", response_model=EmployeeOut)
async def get_employee(employee_id: int, db: AsyncSession = Depends(get_db)):
    query = (
        select(EmployeeORM)
        .filter(EmployeeORM.id == employee_id)
        .options(selectinload(EmployeeORM.projects).selectinload(EmployeeProjectAssignmentORM.project))
    )

    result = await db.execute(query)
    db_employee = result.scalar_one_or_none()

    if not db_employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    projects = [ProjectOut(id=item.project.id, name=item.project.name, parent_id=item.project.parent_id) for item in
                db_employee.projects]

    # Преобразование объектов ORM в Pydantic-модели
    return EmployeeOut(id=db_employee.id, name=db_employee.name, rank=db_employee.rank,
                       projects=projects)


@router.put("/employees/{employee_id}", response_model=EmployeeOut)
async def update_employee(employee_id: int, updated_employee: EmployeeCreate, db: AsyncSession = Depends(get_db)):
    query = (
        select(EmployeeORM)
        .filter(EmployeeORM.id == employee_id)
        .options(selectinload(EmployeeORM.projects).selectinload(EmployeeProjectAssignmentORM.project))
    )

    result = await db.execute(query)
    db_employee = result.scalar_one_or_none()
    projects = [ProjectOut(id=item.project.id, name=item.project.name) for item in
                db_employee.projects]
    db.add(db_employee)
    if not db_employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    db_employee.name = updated_employee.name
    db_employee.rank = updated_employee.rank
    await db.commit()
    await db.refresh(db_employee)
    return EmployeeOut(id=db_employee.id, name=db_employee.name, rank=db_employee.rank,
                       projects=projects)


@router.delete("/employees/{employee_id}")
async def delete_employee(employee_id: int, db: AsyncSession = Depends(get_db)):
    query = (
        select(EmployeeORM)
        .filter(EmployeeORM.id == employee_id)
        .options(selectinload(EmployeeORM.projects))
    )
    result = await db.execute(query)
    db_employee = result.scalar_one_or_none()
    if not db_employee:
        raise HTTPException(status_code=404, detail="EmployeeORM not found")

    await db.delete(db_employee)
    await db.commit()
    return {"message": "Employee deleted successfully"}
