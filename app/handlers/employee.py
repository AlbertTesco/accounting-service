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
from ..services.employee_service import EmployeeService

router = APIRouter()


@router.post("/employees/", response_model=EmployeeOut)
async def create_employee(employee: EmployeeCreate, db: AsyncSession = Depends(get_db)):
    return await EmployeeService.create_employee(employee, db)


@router.get("/employees/", response_model=List[EmployeeOut])
async def get_employees(db: AsyncSession = Depends(database.get_db)):
    return await EmployeeService.get_employees(db)


@router.get("/employees/{employee_id}", response_model=EmployeeOut)
async def get_employee(employee_id: int, db: AsyncSession = Depends(get_db)):
    return await EmployeeService.get_employee(employee_id, db)


@router.put("/employees/{employee_id}", response_model=EmployeeOut)
async def update_employee(employee_id: int, updated_employee: EmployeeCreate, db: AsyncSession = Depends(get_db)):
    return await EmployeeService.update_employee(employee_id, updated_employee, db)


@router.delete("/employees/{employee_id}")
async def delete_employee(employee_id: int, db: AsyncSession = Depends(get_db)):
    return await EmployeeService.delete_employee(employee_id, db)
