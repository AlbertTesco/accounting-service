from typing import List

from fastapi import Depends, HTTPException, APIRouter

from ..schemas.project import ProjectOut, ProjectCreate
from ..services.project_service import ProjectService

router = APIRouter()


@router.get("/projects/", response_model=List[ProjectOut])
async def get_all_projects(service=Depends(ProjectService.get_dependency)):
    try:
        return await service.get_all_projects()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/projects/", response_model=ProjectOut)
async def create_project(project: ProjectCreate, service=Depends(ProjectService.get_dependency)):
    return await service.create_project(project)


@router.get("/projects/{project_id}", response_model=ProjectOut)
async def get_project(project_id: int, service=Depends(ProjectService.get_dependency)):
    return await service.get_project(project_id)


@router.delete("/projects/{project_id}")
async def delete_project(project_id: int, service=Depends(ProjectService.get_dependency)):
    return await service.delete_project(project_id)
