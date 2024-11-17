from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app import database
from app.database import get_db
from app.models import ProjectORM, EmployeeORM, EmployeeProjectAssignmentORM
from app.schemas.assignment import EmployeeProjectAssignmentCreate, EmployeeProjectAssignmentDelete, \
    EmployeeProjectAssignmentByRank
from app.services.assignment_service import AssignmentService
from app.utils.restrictions import is_assignment_allowed

router = APIRouter()


@router.post("/add-employee-to-project")
async def add_employee_to_project(data: EmployeeProjectAssignmentCreate, db: AsyncSession = Depends(get_db)):
    return await AssignmentService.add_employee_to_project(data, db)


@router.delete("/delete-employee-to-project")
async def remove_employee_from_project(data: EmployeeProjectAssignmentDelete,
                                       db: AsyncSession = Depends(database.get_db)):
    return await remove_employee_from_project(data, db)


@router.post("/assign-employees-by-rank/")
async def assign_employees_by_rank(
        assignment_data: EmployeeProjectAssignmentByRank,
        db: AsyncSession = Depends(get_db),
):
    return await AssignmentService.assign_employees_by_rank(assignment_data, db)
