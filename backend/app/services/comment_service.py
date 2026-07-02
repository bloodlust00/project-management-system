from typing import Any, List

from app.exceptions.custom import NotFoundException
from app.models.comment import Comment
from app.repositories.comment_repository import CommentRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.comment import CommentCreate
from app.services.activity_service import ActivityService
from sqlalchemy.ext.asyncio import AsyncSession


class CommentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.comment_repo = CommentRepository(db)
        self.task_repo = TaskRepository(db)
        self.activity_service = ActivityService(db)

    async def get_comment(self, comment_id: Any) -> Comment:
        """Fetch comment, raising NotFound if missing or deleted."""
        comment = await self.comment_repo.get(comment_id)
        if not comment:
            raise NotFoundException("Comment not found.")
        return comment

    async def get_task_comments(self, task_id: Any) -> List[Comment]:
        """Fetch comment thread list for task."""
        # Ensure task exists
        task = await self.task_repo.get(task_id)
        if not task:
            raise NotFoundException("Task not found.")
        return await self.comment_repo.get_comments_for_task(task_id)

    async def create_comment(self, task_id: Any, comment_in: CommentCreate, current_user_id: Any) -> Comment:
        """Post a comment inside task thread and record audit trail logs."""
        task = await self.task_repo.get(task_id)
        if not task:
            raise NotFoundException("Task not found.")

        comment_data = {"content": comment_in.content, "task_id": task_id, "author_id": current_user_id}

        comment = await self.comment_repo.create(comment_data)

        # Log activity
        await self.activity_service.log_activity(
            user_id=current_user_id,
            action="CREATE",
            entity_type="COMMENT",
            entity_id=comment.id,
            details={"task_id": str(task_id)},
        )

        # Reload to load author info
        return await self.get_comment(comment.id)

    async def delete_comment(self, comment_id: Any, current_user_id: Any) -> Comment:
        """Delete specific comment entry and write audit log records."""
        comment = await self.get_comment(comment_id)

        await self.comment_repo.remove(id=comment_id)

        # Log activity
        await self.activity_service.log_activity(
            user_id=current_user_id,
            action="DELETE",
            entity_type="COMMENT",
            entity_id=comment_id,
            details={"task_id": str(comment.task_id)},
        )
        return comment
