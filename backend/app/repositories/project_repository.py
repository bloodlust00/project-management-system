from typing import List, Optional, Any
from sqlalchemy import select, or_, func
from sqlalchemy.orm import selectinload
from app.repositories.base import BaseRepository
from app.models.project import Project

class ProjectRepository(BaseRepository[Project]):
    def __init__(self, db):
        super().__init__(Project, db)

    async def get_project_with_owner(self, project_id: Any) -> Optional[Project]:
        """Fetch project details along with owner information."""
        query = select(Project).filter(Project.id == project_id, Project.is_deleted == False).options(selectinload(Project.owner))
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_projects_paginated(
        self,
        *,
        skip: int = 0,
        limit: int = 10,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> tuple[List[Project], int]:
        """Fetch paginated projects matching optional search query."""
        query = select(Project).filter(Project.is_deleted == False)

        if search:
            query = query.filter(
                or_(
                    Project.name.ilike(f"%{search}%"),
                    Project.description.ilike(f"%{search}%")
                )
            )

        # Count before limit/offset
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar() or 0

        # Apply sorting
        if hasattr(Project, sort_by):
            sort_attr = getattr(Project, sort_by)
            if sort_order.lower() == "desc":
                query = query.order_by(sort_attr.desc())
            else:
                query = query.order_by(sort_attr.asc())
        else:
            query = query.order_by(Project.created_at.desc())

        # Load owner information automatically
        query = query.options(selectinload(Project.owner)).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all()), total_count
