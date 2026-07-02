from typing import Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.activity_repository import ActivityRepository
from app.models.activity import ActivityLog

class ActivityService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.activity_repo = ActivityRepository(db)

    async def log_activity(
        self,
        user_id: Optional[Any],
        action: str,
        entity_type: str,
        entity_id: Optional[Any] = None,
        details: Optional[dict] = None
    ) -> ActivityLog:
        """Asynchronously writes a system audit action detail log."""
        log_data = {
            "user_id": user_id,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "details": details
        }
        return await self.activity_repo.create(log_data)

    async def get_logs(
        self,
        *,
        user_id: Optional[Any] = None,
        entity_type: Optional[str] = None,
        action: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[List[ActivityLog], int]:
        """Fetch audit timeline records using filters."""
        return await self.activity_repo.get_logs_paginated(
            user_id=user_id,
            entity_type=entity_type,
            action=action,
            skip=skip,
            limit=limit
        )
