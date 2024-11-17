from typing import List, Optional

from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str
    parent_id: Optional[int] = None

    class Config:
        from_attributes = True


class ProjectDelete(BaseModel):
    id: int


class ProjectOut(BaseModel):
    id: int
    name: str
    parent_id: Optional[int] = None
    parent_project: Optional['ProjectOut'] = None
    subprojects: List['ProjectOut'] = []

    class Config:
        from_attributes = True


ProjectOut.model_rebuild()
