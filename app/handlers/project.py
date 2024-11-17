from typing import List

from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas.project import ProjectOut, ProjectCreate
from ..services.project_service import ProjectService

router = APIRouter()


@router.get("/projects/", response_model=List[ProjectOut])
async def get_all_projects(db: AsyncSession = Depends(get_db)):
    try:
        return await ProjectService.get_all_projects(db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/projects/", response_model=ProjectOut)
async def create_project(project: ProjectCreate, db: AsyncSession = Depends(get_db)):
    return await ProjectService.create_project(project, db)


@router.get("/projects/{project_id}", response_model=ProjectOut)
async def get_project(project_id: int, db: AsyncSession = Depends(get_db)):
    return await ProjectService.get_project(project_id, db)


@router.delete("/projects/{project_id}")
async def delete_project(project_id: int, db: AsyncSession = Depends(get_db)):
    return await ProjectService.delete_project(project_id, db)
