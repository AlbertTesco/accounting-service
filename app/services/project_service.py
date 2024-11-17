from typing import List

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from ..models import ProjectORM
from ..schemas.project import ProjectOut, ProjectCreate


class ProjectService:
    @staticmethod
    async def get_all_projects(db: AsyncSession) -> List[ProjectOut]:
        """
        Получает список всех верхнеуровневых проектов с их подпроектами.
        """
        # Получение верхнеуровневых проектов
        result = await db.execute(
            select(ProjectORM)
            .options(selectinload(ProjectORM.parent))
            .filter(ProjectORM.parent_id.is_(None))
        )
        db_projects = result.scalars().all()

        if not db_projects:
            raise ValueError("No projects found")

        projects_out = []

        for project in db_projects:
            # Получение подпроектов для текущего верхнеуровневого проекта
            subprojects = await db.execute(
                select(ProjectORM).filter(ProjectORM.parent_id == project.id)
            )
            subprojects = subprojects.scalars().all()

            # Формируем вложенные подпроекты
            subproject_outs = [
                ProjectOut(id=sub.id, name=sub.name, parent_id=sub.parent_id)
                for sub in subprojects
            ]

            # Формируем верхнеуровневый проект с вложенными подпроектами
            project_out = ProjectOut(
                id=project.id,
                name=project.name,
                parent_id=project.parent_id,
                parent_project=None,
                subprojects=subproject_outs
            )

            projects_out.append(project_out)

        return projects_out

    @staticmethod
    async def create_project(project: ProjectCreate, db: AsyncSession) -> ProjectOut:
        """
        Создает новый проект.
        """
        # Создание объекта ORM
        db_project = ProjectORM(name=project.name, parent_id=project.parent_id)
        db.add(db_project)

        # Коммит изменений и обновление объекта
        await db.commit()
        await db.refresh(db_project)

        # Возврат объекта схемы
        return ProjectOut(
            id=db_project.id,
            name=db_project.name,
            parent_id=db_project.parent_id
        )

    @staticmethod
    async def get_project(project_id: int, db: AsyncSession) -> ProjectOut:
        """
        Получает проект с указанным ID, включая родительский и дочерние проекты.
        """
        # Запрос проекта с родителем и дочерними проектами
        query = (
            select(ProjectORM)
            .filter(ProjectORM.id == project_id)
            .options(selectinload(ProjectORM.parent), selectinload(ProjectORM.subprojects))
        )
        result = await db.execute(query)
        db_project = result.scalar_one_or_none()

        if db_project is None:
            raise HTTPException(status_code=404, detail="Project not found")

        # Если проект зависимый, добавляем родительский проект
        if db_project.parent_id is not None:
            return ProjectOut(
                id=db_project.id,
                name=db_project.name,
                parent_id=db_project.parent_id,
                parent_project=ProjectOut(
                    id=db_project.parent.id,
                    name=db_project.parent.name,
                    parent_id=db_project.parent.parent_id
                )
            )

        # Если проект основной, добавляем дочерние проекты
        subprojects = [
            ProjectOut(id=sub.id, name=sub.name, parent_id=sub.parent_id) for sub in db_project.subprojects
        ]
        return ProjectOut(
            id=db_project.id,
            name=db_project.name,
            parent_id=db_project.parent_id,
            subprojects=subprojects
        )

    @staticmethod
    async def delete_project(project_id: int, db: AsyncSession) -> dict:
        """
        Удаляет проект с указанным ID.
        """
        # Поиск проекта
        result = await db.execute(select(ProjectORM).filter(ProjectORM.id == project_id))
        db_project = result.scalar_one_or_none()

        if db_project is None:
            raise HTTPException(status_code=404, detail="Project not found")

        # Удаление проекта
        await db.delete(db_project)
        await db.commit()
        return {"message": "Project deleted successfully"}
