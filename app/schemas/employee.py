from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

from app.schemas.project import ProjectOut


class Rank(str, Enum):
    RANK_1 = "1"
    RANK_2 = "2"
    RANK_3 = "3"
    RANK_4 = "4"


class EmployeeCreate(BaseModel):
    name: str
    rank: Rank

    class Config:
        from_attributes = True


class EmployeeOut(BaseModel):
    id: int
    name: str
    rank: Rank
    projects: Optional[List['ProjectOut']] = []

    class Config:
        from_attributes = True