from fastapi import Depends, APIRouter

from app.schemas.assignment import EmployeeProjectAssignmentCreate, EmployeeProjectAssignmentDelete, \
    EmployeeProjectAssignmentByRank
from app.services.assignment_service import AssignmentService

router = APIRouter()


@router.post("/add-employee-to-project")
async def add_employee_to_project(data: EmployeeProjectAssignmentCreate,
                                  service=Depends(AssignmentService.get_dependency)):
    return await service.add_employee_to_project(data)


@router.delete("/delete-employee-to-project")
async def remove_employee_from_project(data: EmployeeProjectAssignmentDelete,
                                       service=Depends(AssignmentService.get_dependency)):
    return await service.remove_employee_from_project(data)


@router.post("/assign-employees-by-rank/")
async def assign_employees_by_rank(
        assignment_data: EmployeeProjectAssignmentByRank,
        service=Depends(AssignmentService.get_dependency),
):
    return await service.assign_employees_by_rank(assignment_data)
