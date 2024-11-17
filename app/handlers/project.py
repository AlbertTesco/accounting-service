from typing import List

from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models import ProjectORM
from ..schemas.project import ProjectOut, ProjectCreate, ProjectDelete

router = APIRouter()


@router.get("/projects/", response_model=List[ProjectOut])
async def get_all_projects(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ProjectORM)
        .options(selectinload(ProjectORM.parent))
        .filter(ProjectORM.parent_id.is_(None))
    )
    db_projects = result.scalars().all()

    if not db_projects:
        raise HTTPException(status_code=404, detail="No projects found")

    projects_out = []

    for project in db_projects:
        # Получаем дочерние проекты для текущего родительского проекта
        subprojects = await db.execute(
            select(ProjectORM).filter(ProjectORM.parent_id == project.id)
        )
        subprojects = subprojects.scalars().all()

        subproject_outs = [
            ProjectOut(id=sub.id, name=sub.name, parent_id=sub.parent_id)
            for sub in subprojects
        ]

        project_out = ProjectOut(
            id=project.id,
            name=project.name,
            parent_id=project.parent_id,
            parent_project=None,
            subprojects=subproject_outs
        )

        projects_out.append(project_out)

    return projects_out


@router.post("/projects/", response_model=ProjectOut)
async def create_project(project: ProjectCreate, db: AsyncSession = Depends(get_db)):
    db_project = ProjectORM(name=project.name, parent_id=project.parent_id)
    db.add(db_project)

    await db.commit()
    await db.refresh(db_project)

    # Загрузка субпроектов (если они есть)
    # statement = select(ProjectORM).options(selectinload(ProjectORM.subprojects)).filter(ProjectORM.id == db_project.id)
    # result = await db.execute(statement)
    # project_with_subprojects = result.scalar_one()

    return ProjectOut(id=db_project.id, name=project.name, parent_id=project.parent_id)


@router.get("/projects/{project_id}", response_model=ProjectOut)
async def get_project(project_id: int, db: AsyncSession = Depends(get_db)):
    # Выполнение асинхронного запроса с использованием selectinload для загрузки связанных данных
    query = (
        select(ProjectORM)
        .filter(ProjectORM.id == project_id)
        .options(selectinload(ProjectORM.parent), selectinload(ProjectORM.subprojects))
    )
    result = await db.execute(query)
    db_project = result.scalar_one_or_none()

    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    # Если проект зависимый, выводим его с родительским проектом
    if db_project.parent_id is not None:
        return ProjectOut(
            id=db_project.id,
            name=db_project.name,
            parent_id=db_project.parent_id,
            parent_project=ProjectOut(id=db_project.parent.id, name=db_project.parent.name,
                                      parent_id=db_project.parent.id)
        )

    # Если проект основной, выводим его с дочерними проектами
    subprojects = [ProjectOut(id=sub.id, name=sub.name, parent_id=sub.id) for sub in db_project.subprojects]
    return ProjectOut(id=db_project.id, name=db_project.name, subprojects=subprojects)


@router.delete("/projects/")
async def delete_project(project: ProjectDelete, db: AsyncSession = Depends(get_db)):
    # Асинхронный запрос на поиск проекта
    result = await db.execute(select(ProjectORM).filter(ProjectORM.id == project.id))
    db_project = result.scalar_one_or_none()

    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    # Асинхронные операции удаления и коммита
    await db.delete(db_project)
    await db.commit()
    return {"message": "Project deleted successfully"}
