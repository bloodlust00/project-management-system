from typing import Any, List, Optional

from app.core.logging import logger
from app.core.redis import redis_client
from app.exceptions.custom import NotFoundException
from app.models.project import Project
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.services.activity_service import ActivityService
from sqlalchemy.ext.asyncio import AsyncSession


class ProjectService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.project_repo = ProjectRepository(db)
        self.activity_service = ActivityService(db)

    async def get_project(self, project_id: Any) -> Project:
        """Fetch project details, raising NotFound if missing or deleted."""
        project = await self.project_repo.get_project_with_owner(project_id)
        if not project:
            raise NotFoundException("Project not found.")
        return project

    async def get_projects(
        self,
        *,
        skip: int = 0,
        limit: int = 10,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[List[dict], int]:
        """Fetch paginated projects. Integrates Redis caching for queries."""
        cache_key = (
            f"projects:list:skip={skip}:limit={limit}:search={search or ''}:sort_by={sort_by}:sort_order={sort_order}"
        )

        # Check cache
        cached_data = await redis_client.get_cache(cache_key)
        if cached_data:
            logger.info(f"Cache HIT for key: {cache_key}")
            return cached_data["items"], cached_data["total"]

        logger.info(f"Cache MISS for key: {cache_key}. Fetching from DB.")
        projects, total = await self.project_repo.get_projects_paginated(
            skip=skip, limit=limit, search=search, sort_by=sort_by, sort_order=sort_order
        )

        # Serialize using Pydantic schema for caching compatibility
        serialized_projects = [ProjectResponse.model_validate(p).model_dump(mode="json") for p in projects]

        # Write to cache
        cache_payload = {"items": serialized_projects, "total": total}
        await redis_client.set_cache(cache_key, cache_payload, expire_seconds=300)

        return serialized_projects, total

    async def create_project(self, project_in: ProjectCreate, current_user_id: Any) -> Project:
        """Create project, invalidate list caches, and record audit details."""
        project_data = project_in.model_dump()
        project_data["owner_id"] = current_user_id

        project = await self.project_repo.create(project_data)

        # Invalidate related cache patterns
        await redis_client.delete_by_pattern("projects:list:*")
        # Invalidate dashboard metrics cache
        await redis_client.delete_cache("dashboard:stats")

        # Eager load owner info
        project = await self.project_repo.get_project_with_owner(project.id)

        # Log activity
        await self.activity_service.log_activity(
            user_id=current_user_id,
            action="CREATE",
            entity_type="PROJECT",
            entity_id=project.id,
            details={"name": project.name},
        )

        return project

    async def update_project(self, project_id: Any, project_in: ProjectUpdate, current_user_id: Any) -> Project:
        """Update project parameters, invalidate list caches, and log updates."""
        project = await self.get_project(project_id)

        # Enforce Ownership checks if not Admin/Manager (roles check is managed by router RBAC dependencies,
        # but service maintains strict boundaries)
        # Note: RBAC middleware blocks this beforehand, but service check is a secondary fail-safe.

        update_data = project_in.model_dump(exclude_unset=True)
        updated_project = await self.project_repo.update(db_obj=project, obj_in=update_data)

        # Invalidate cache patterns
        await redis_client.delete_by_pattern("projects:list:*")
        await redis_client.delete_cache("dashboard:stats")

        # Log activity
        await self.activity_service.log_activity(
            user_id=current_user_id,
            action="UPDATE",
            entity_type="PROJECT",
            entity_id=project_id,
            details={"updated_fields": list(update_data.keys())},
        )
        return updated_project

    async def delete_project(self, project_id: Any, current_user_id: Any) -> Project:
        """Soft-delete project, invalidate list caches, and log deletions."""
        project = await self.get_project(project_id)

        await self.project_repo.remove(id=project_id)

        # Invalidate cache patterns
        await redis_client.delete_by_pattern("projects:list:*")
        await redis_client.delete_cache("dashboard:stats")

        # Log activity
        await self.activity_service.log_activity(
            user_id=current_user_id, action="DELETE", entity_type="PROJECT", entity_id=project_id
        )
        return project
