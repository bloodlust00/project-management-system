from typing import List, Optional, Any
from sqlalchemy import select, or_, func
from sqlalchemy.orm import selectinload
from app.repositories.base import BaseRepository
from app.models.task import Task, TaskStatus, TaskPriority

class TaskRepository(BaseRepository[Task]):
    def __init__(self, db):
        super().__init__(Task, db)

    async def get_task_details(self, task_id: Any) -> Optional[Task]:
        """Fetch task details along with project and assignees information."""
        query = (
            select(Task)
            .filter(Task.id == task_id, Task.is_deleted == False)
            .options(selectinload(Task.project), selectinload(Task.assignees))
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_tasks_paginated(
        self,
        *,
        project_id: Optional[Any] = None,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        search: Optional[str] = None,
        assignee_id: Optional[Any] = None,
        skip: int = 0,
        limit: int = 10,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> tuple[List[Task], int]:
        """Fetch paginated tasks with multiple filtering parameters."""
        query = select(Task).filter(Task.is_deleted == False)

        if project_id:
            query = query.filter(Task.project_id == project_id)
        if status:
            query = query.filter(Task.status == status)
        if priority:
            query = query.filter(Task.priority == priority)
        if assignee_id:
            # Check if assignee_id is in assignees list (requires join)
            query = query.filter(Task.assignees.any(id=assignee_id))
        if search:
            query = query.filter(
                or_(
                    Task.title.ilike(f"%{search}%"),
                    Task.description.ilike(f"%{search}%")
                )
            )

        # Count before limits
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar() or 0

        # Sorting
        if hasattr(Task, sort_by):
            sort_attr = getattr(Task, sort_by)
            if sort_order.lower() == "desc":
                query = query.order_by(sort_attr.desc())
            else:
                query = query.order_by(sort_attr.asc())
        else:
            query = query.order_by(Task.created_at.desc())

        query = query.options(selectinload(Task.assignees)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total_count
