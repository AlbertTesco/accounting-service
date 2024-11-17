from typing import List

from fastapi import Depends, APIRouter

from ..schemas.employee import EmployeeCreate, EmployeeOut
from ..services.employee_service import EmployeeService

router = APIRouter()


@router.post("/employees/", response_model=EmployeeOut)
async def create_employee(employee: EmployeeCreate, service=Depends(EmployeeService.get_dependency)):
    return await service.create_employee(employee)


@router.get("/employees/", response_model=List[EmployeeOut])
async def get_employees(service=Depends(EmployeeService.get_dependency)):
    return await service.get_employees()


@router.get("/employees/{employee_id}", response_model=EmployeeOut)
async def get_employee(employee_id: int, service=Depends(EmployeeService.get_dependency)):
    return await service.get_employee(employee_id)


@router.put("/employees/{employee_id}", response_model=EmployeeOut)
async def update_employee(employee_id: int, updated_employee: EmployeeCreate,
                          service=Depends(EmployeeService.get_dependency)):
    return await service.update_employee(employee_id, updated_employee)


@router.delete("/employees/{employee_id}")
async def delete_employee(employee_id: int, service=Depends(EmployeeService.get_dependency)):
    return await service.delete_employee(employee_id)
