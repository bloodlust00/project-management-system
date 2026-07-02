import io
import csv
from typing import List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.services.activity_service import ActivityService
from app.core.redis import redis_client
from app.exceptions.custom import NotFoundException, BadRequestException
from app.schemas.task import TaskCreate, TaskUpdate
from app.models.task import Task, TaskStatus, TaskPriority
from app.core.logging import logger

class TaskService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.task_repo = TaskRepository(db)
        self.user_repo = UserRepository(db)
        self.activity_service = ActivityService(db)

    async def get_task(self, task_id: Any) -> Task:
        """Fetch task details, raising NotFound if missing or deleted."""
        task = await self.task_repo.get_task_details(task_id)
        if not task:
            raise NotFoundException("Task not found.")
        return task

    async def get_tasks(
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
        """Fetch tasks with filtering and pagination parameters."""
        return await self.task_repo.get_tasks_paginated(
            project_id=project_id,
            status=status,
            priority=priority,
            search=search,
            assignee_id=assignee_id,
            skip=skip,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order
        )

    async def create_task(self, project_id: Any, task_in: TaskCreate, current_user_id: Any) -> Task:
        """Create a new task, maps assignee UUIDs, and clears cache."""
        task_data = task_in.model_dump(exclude={"assignee_ids"})
        task_data["project_id"] = project_id

        # Instantiate task
        task = await self.task_repo.create(task_data)

        # Handle assignees if passed
        if task_in.assignee_ids:
            users = await self.user_repo.get_by_ids(task_in.assignee_ids)
            if len(users) != len(task_in.assignee_ids):
                found_ids = {u.id for u in users}
                missing_ids = [str(uid) for uid in task_in.assignee_ids if uid not in found_ids]
                raise NotFoundException(f"Assignee users with IDs {', '.join(missing_ids)} not found.")
            for user in users:
                task.assignees.append(user)
            try:
                await self.db.commit()
                await self.db.refresh(task)
            except Exception as e:
                await self.db.rollback()
                raise e

        # Clear stats cache
        await redis_client.delete_cache("dashboard:stats")

        # Log activity
        await self.activity_service.log_activity(
            user_id=current_user_id,
            action="CREATE",
            entity_type="TASK",
            entity_id=task.id,
            details={"title": task.title, "project_id": str(project_id)}
        )

        return await self.get_task(task.id)

    async def update_task(self, task_id: Any, task_in: TaskUpdate, current_user_id: Any) -> Task:
        """Update task properties, remaps assignee associations if passed, and logs edits."""
        task = await self.get_task(task_id)

        update_data = task_in.model_dump(exclude_unset=True, exclude={"assignee_ids"})
        
        # Apply updates
        task = await self.task_repo.update(db_obj=task, obj_in=update_data)

        # Re-map assignees list if provided
        if task_in.assignee_ids is not None:
            task.assignees.clear()
            if task_in.assignee_ids:
                users = await self.user_repo.get_by_ids(task_in.assignee_ids)
                if len(users) != len(task_in.assignee_ids):
                    found_ids = {u.id for u in users}
                    missing_ids = [str(uid) for uid in task_in.assignee_ids if uid not in found_ids]
                    raise NotFoundException(f"Assignee users with IDs {', '.join(missing_ids)} not found.")
                for user in users:
                    task.assignees.append(user)
            try:
                await self.db.commit()
                await self.db.refresh(task)
            except Exception as e:
                await self.db.rollback()
                raise e

        # Invalidate cache
        await redis_client.delete_cache("dashboard:stats")

        # Log activity
        await self.activity_service.log_activity(
            user_id=current_user_id,
            action="UPDATE",
            entity_type="TASK",
            entity_id=task_id,
            details={"updated_fields": list(task_in.model_dump(exclude_unset=True).keys())}
        )

        return await self.get_task(task_id)

    async def delete_task(self, task_id: Any, current_user_id: Any) -> Task:
        """Soft delete task, invalidate statistics caches, and log delete activity."""
        task = await self.get_task(task_id)

        await self.task_repo.remove(id=task_id)

        # Clear stats cache
        await redis_client.delete_cache("dashboard:stats")

        # Log activity
        await self.activity_service.log_activity(
            user_id=current_user_id,
            action="DELETE",
            entity_type="TASK",
            entity_id=task_id
        )
        return task

    async def export_tasks_to_csv(self, project_id: Optional[Any] = None) -> str:
        """Query tasks and formats output as a string containing CSV data."""
        # Query matching records
        tasks, _ = await self.task_repo.get_tasks_paginated(
            project_id=project_id,
            limit=5000  # Max bounds for sheet dump
        )

        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write CSV Headers
        writer.writerow(["Task ID", "Title", "Status", "Priority", "Due Date", "Project ID", "Assignees", "Created At"])
        
        for task in tasks:
            assignee_names = ", ".join([u.full_name for u in task.assignees])
            writer.writerow([
                str(task.id),
                task.title,
                task.status.value,
                task.priority.value,
                task.due_date.isoformat() if task.due_date else "N/A",
                str(task.project_id),
                assignee_names,
                task.created_at.isoformat()
            ])
            
        return output.getvalue()
