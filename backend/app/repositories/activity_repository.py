from typing import List, Optional, Any
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.repositories.base import BaseRepository
from app.models.activity import ActivityLog

class ActivityRepository(BaseRepository[ActivityLog]):
    def __init__(self, db):
        super().__init__(ActivityLog, db)

    async def get_logs_paginated(
        self,
        *,
        user_id: Optional[Any] = None,
        entity_type: Optional[str] = None,
        action: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[List[ActivityLog], int]:
        """Fetch paginated audit activity logs with filters."""
        query = select(ActivityLog)

        if user_id:
            query = query.filter(ActivityLog.user_id == user_id)
        if entity_type:
            query = query.filter(ActivityLog.entity_type == entity_type)
        if action:
            query = query.filter(ActivityLog.action == action)

        # Count total records
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar() or 0

        # Sort by creation time descending (most recent first)
        query = query.order_by(ActivityLog.created_at.desc()).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all()), total_count
