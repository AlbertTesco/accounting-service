from app import models
from app.models import EmployeeORM, ProjectORM, EmployeeProjectAssignmentORM
from app.schemas.assignment import EmployeeProjectAssignmentCreate, EmployeeProjectAssignmentDelete, \
    EmployeeProjectAssignmentByRank
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException

from app.utils.restrictions import is_assignment_allowed


class AssignmentService:

    @staticmethod
    async def add_employee_to_project(data: EmployeeProjectAssignmentCreate, db: AsyncSession):
        query = (
            select(ProjectORM)
            .filter(ProjectORM.id == data.project_id)
        )
        result = await db.execute(query)
        db_project = result.scalar_one_or_none()
        if not db_project:
            raise HTTPException(status_code=404, detail="Project not found")

        query = (
            select(EmployeeORM)
            .filter(EmployeeORM.id == data.employee_id)
        )
        result = await db.execute(query)
        db_employee = result.scalar_one_or_none()
        if not db_employee:
            raise HTTPException(status_code=404, detail="Employee not found")

        query = (
            select(models.EmployeeProjectAssignmentORM)
            .filter(models.EmployeeProjectAssignmentORM.project_id == data.project_id,
                    models.EmployeeProjectAssignmentORM.employee_id == data.employee_id)
        )
        result = await db.execute(query)
        existing_assignment = result.scalar_one_or_none()

        if existing_assignment:
            raise HTTPException(status_code=400, detail="EmployeeORM already assigned to this project")

        if not data.ignore_conflicts:
            is_allowed, conflict_reason = await is_assignment_allowed(db=db, employee=db_employee, project=db_project)
            if not is_allowed:
                raise HTTPException(status_code=400, detail=conflict_reason)

        new_assignment = models.EmployeeProjectAssignmentORM(employee_id=data.employee_id, project_id=data.project_id)

        db.add(new_assignment)
        await db.commit()

        return {"message": "Employee added to project successfully"}

    @staticmethod
    async def remove_employee_from_project(data: EmployeeProjectAssignmentDelete, db: AsyncSession):
        query = (
            select(ProjectORM)
            .filter(ProjectORM.id == data.project_id)
        )
        result = await db.execute(query)
        db_project = result.scalar_one_or_none()
        if not db_project:
            raise HTTPException(status_code=404, detail="Project not found")

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

    @staticmethod
    async def assign_employees_by_rank(assignment_data: EmployeeProjectAssignmentByRank, db: AsyncSession):
        result = await db.execute(select(ProjectORM).filter(ProjectORM.id == assignment_data.project_id))
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        result = await db.execute(select(EmployeeORM).filter(EmployeeORM.rank == assignment_data.rank))
        employees = result.scalars().all()

        if not employees:
            raise HTTPException(status_code=404, detail=f"No employees with rank {assignment_data.rank} found")

        skipped_employees = []
        for employee in employees:
            is_allowed, conflict_details = await is_assignment_allowed(db, employee, project)

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
            db.add(new_assignment)

        await db.commit()

        return {
            "message": f"Employees with rank {assignment_data.rank} processed for project {assignment_data.project_id}",
            "skipped_employees": skipped_employees,
        }