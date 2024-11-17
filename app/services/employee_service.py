from fastapi import HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app import models
from app.database import get_db
from app.models import EmployeeORM, EmployeeProjectAssignmentORM
from app.schemas.employee import EmployeeCreate, EmployeeOut
from app.schemas.project import ProjectOut


class EmployeeService:

    def __init__(self, db):
        self.db = db

    @classmethod
    def get_dependency(cls, db: AsyncSession = Depends(get_db)):
        return cls(db)

    async def create_employee(self, employee: EmployeeCreate) -> EmployeeOut:
        db_employee = models.EmployeeORM(name=employee.name, rank=employee.rank)
        self.db.add(db_employee)
        await self.db.commit()
        await self.db.refresh(db_employee)
        return EmployeeOut(id=db_employee.id, name=db_employee.name, rank=db_employee.rank, projects=[])

    async def get_employees(self):
        query = (
            select(EmployeeORM)
            .options(selectinload(EmployeeORM.projects).selectinload(EmployeeProjectAssignmentORM.project))
        )
        result = await self.db.execute(query)
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

    async def get_employee(self, employee_id: int) -> EmployeeOut:
        query = (
            select(EmployeeORM)
            .filter(EmployeeORM.id == employee_id)
            .options(selectinload(EmployeeORM.projects).selectinload(EmployeeProjectAssignmentORM.project))
        )

        result = await self.db.execute(query)
        db_employee = result.scalar_one_or_none()

        if not db_employee:
            raise HTTPException(status_code=404, detail="Employee not found")

        projects = [ProjectOut(id=item.project.id, name=item.project.name, parent_id=item.project.parent_id) for item in
                    db_employee.projects]

        return EmployeeOut(id=db_employee.id, name=db_employee.name, rank=db_employee.rank, projects=projects)

    async def update_employee(self, employee_id: int, updated_employee: EmployeeCreate):
        query = (
            select(EmployeeORM)
            .filter(EmployeeORM.id == employee_id)
            .options(selectinload(EmployeeORM.projects).selectinload(EmployeeProjectAssignmentORM.project))
        )

        result = await self.db.execute(query)
        db_employee = result.scalar_one_or_none()
        projects = [ProjectOut(id=item.project.id, name=item.project.name) for item in
                    db_employee.projects]
        self.db.add(db_employee)
        if not db_employee:
            raise HTTPException(status_code=404, detail="Employee not found")

        db_employee.name = updated_employee.name
        db_employee.rank = updated_employee.rank
        await self.db.commit()
        await self.db.refresh(db_employee)
        return EmployeeOut(id=db_employee.id, name=db_employee.name, rank=db_employee.rank,
                           projects=projects)

    async def delete_employee(self, employee_id: int):
        query = (
            select(EmployeeORM)
            .filter(EmployeeORM.id == employee_id)
            .options(selectinload(EmployeeORM.projects))
        )
        result = await self.db.execute(query)
        db_employee = result.scalar_one_or_none()
        if not db_employee:
            raise HTTPException(status_code=404, detail="EmployeeORM not found")

        await self.db.delete(db_employee)
        await self.db.commit()
        return {"message": "Employee deleted successfully"}
