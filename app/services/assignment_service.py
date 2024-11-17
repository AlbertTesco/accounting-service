from fastapi import HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app import models
from app.database import get_db
from app.models import EmployeeORM, ProjectORM, EmployeeProjectAssignmentORM
from app.schemas.assignment import EmployeeProjectAssignmentCreate, EmployeeProjectAssignmentDelete, \
    EmployeeProjectAssignmentByRank
from app.utils.restrictions import is_assignment_allowed


class AssignmentService:

    def __init__(self, db: AsyncSession):
        self.db = db

    @classmethod
    def get_dependency(cls, db: AsyncSession = Depends(get_db)):
        return cls(db)

    async def add_employee_to_project(self, data: EmployeeProjectAssignmentCreate):
        query = (
            select(ProjectORM)
            .filter(ProjectORM.id == data.project_id)
        )
        result = await self.db.execute(query)
        db_project = result.scalar_one_or_none()
        if not db_project:
            raise HTTPException(status_code=404, detail="Project not found")

        query = (
            select(EmployeeORM)
            .filter(EmployeeORM.id == data.employee_id)
        )
        result = await self.db.execute(query)
        db_employee = result.scalar_one_or_none()
        if not db_employee:
            raise HTTPException(status_code=404, detail="Employee not found")

        query = (
            select(models.EmployeeProjectAssignmentORM)
            .filter(models.EmployeeProjectAssignmentORM.project_id == data.project_id,
                    models.EmployeeProjectAssignmentORM.employee_id == data.employee_id)
        )
        result = await self.db.execute(query)
        existing_assignment = result.scalar_one_or_none()

        if existing_assignment:
            raise HTTPException(status_code=400, detail="EmployeeORM already assigned to this project")

        if not data.ignore_conflicts:
            is_allowed, conflict_reason = await is_assignment_allowed(db=self.db, employee=db_employee,
                                                                      project=db_project)
            if not is_allowed:
                raise HTTPException(status_code=400, detail=conflict_reason)

        new_assignment = models.EmployeeProjectAssignmentORM(employee_id=data.employee_id, project_id=data.project_id)

        self.db.add(new_assignment)
        await self.db.commit()

        return {"message": "Employee added to project successfully"}

    async def remove_employee_from_project(self, data: EmployeeProjectAssignmentDelete):
        query = (
            select(ProjectORM)
            .filter(ProjectORM.id == data.project_id)
        )
        result = await self.db.execute(query)
        db_project = result.scalar_one_or_none()
        if not db_project:
            raise HTTPException(status_code=404, detail="Project not found")

        query = (
            select(EmployeeORM)
            .filter(EmployeeORM.id == data.employee_id)
        )
        result = await self.db.execute(query)
        db_employee = result.scalar_one_or_none()

        if not db_employee:
            raise HTTPException(status_code=404, detail="EmployeeORM not found")

        query = (
            select(EmployeeProjectAssignmentORM)
            .filter(EmployeeProjectAssignmentORM.project_id == data.project_id,
                    EmployeeProjectAssignmentORM.employee_id == data.employee_id)
        )

        result = await self.db.execute(query)
        existing_assignment = result.scalar_one_or_none()

        if not existing_assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")

        await self.db.delete(existing_assignment)
        await self.db.commit()
        return {"message": "Employee removed from project successfully"}

    async def assign_employees_by_rank(self, assignment_data: EmployeeProjectAssignmentByRank):
        result = await self.db.execute(select(ProjectORM).filter(ProjectORM.id == assignment_data.project_id))
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        result = await self.db.execute(select(EmployeeORM).filter(EmployeeORM.rank == assignment_data.rank))
        employees = result.scalars().all()

        if not employees:
            raise HTTPException(status_code=404, detail=f"No employees with rank {assignment_data.rank} found")

        skipped_employees = []
        for employee in employees:
            is_allowed, conflict_details = await is_assignment_allowed(self.db, employee, project)

            if not is_allowed and not assignment_data.ignore_conflicts:
                skipped_employees.append({
                    "employee_id": employee.id,
                    "name": employee.name,
                    "conflict_details": conflict_details,
                })
                continue

            new_assignment = EmployeeProjectAssignmentORM(
                employee_id=employee.id,
                project_id=project.id,
            )
            self.db.add(new_assignment)

        await self.db.commit()

        return {
            "message": f"Employees with rank {assignment_data.rank} processed for project {assignment_data.project_id}",
            "skipped_employees": skipped_employees,
        }
