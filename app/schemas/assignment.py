from typing import Optional

from pydantic import BaseModel


class EmployeeProjectAssignmentCreate(BaseModel):
    project_id: int
    employee_id: int
    ignore_conflicts: Optional[bool] = False

class EmployeeProjectAssignmentByRank(BaseModel):
    project_id: int
    rank: str
    ignore_conflicts: Optional[bool] = False

class EmployeeProjectAssignmentDelete(BaseModel):
    project_id: int
    employee_id: int

