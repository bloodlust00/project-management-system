from typing import Any, List

from app.models.comment import Comment
from app.repositories.base import BaseRepository
from sqlalchemy import select
from sqlalchemy.orm import selectinload


class CommentRepository(BaseRepository[Comment]):
    def __init__(self, db):
        super().__init__(Comment, db)

    async def get_comments_for_task(self, task_id: Any) -> List[Comment]:
        """Fetch all comments mapped to a task, loading author information."""
        query = (
            select(Comment)
            .filter(Comment.task_id == task_id, Comment.is_deleted.is_(False))
            .options(selectinload(Comment.author))
            .order_by(Comment.created_at.asc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
