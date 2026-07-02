import uuid
from typing import Optional

from app.dependencies.auth import PermissionChecker, get_current_user
from app.dependencies.db import get_db
from app.models.user import User
from app.schemas.common import APIResponse, PaginatedData, PaginationMeta
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.services.project_service import ProjectService
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("/", response_model=APIResponse[PaginatedData[ProjectResponse]])
async def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=1000),
    search: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieves paginated, filterable projects list (integrates Redis cache checks)."""
    project_service = ProjectService(db)
    items, total = await project_service.get_projects(
        skip=skip, limit=limit, search=search, sort_by=sort_by, sort_order=sort_order
    )

    pages = (total + limit - 1) // limit if limit > 0 else 0
    return APIResponse[PaginatedData[ProjectResponse]](
        success=True,
        message="Projects list retrieved successfully",
        data=PaginatedData(
            items=items, pagination=PaginationMeta(total=total, page=(skip // limit) + 1, size=limit, pages=pages)
        ),
    )


@router.post(
    "/", response_model=APIResponse[ProjectResponse], dependencies=[Depends(PermissionChecker(["project:create"]))]
)
async def create_project(
    project_in: ProjectCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Creates a new project (requires project:create permission)."""
    project_service = ProjectService(db)
    project = await project_service.create_project(project_in, current_user.id)
    return APIResponse[ProjectResponse](
        success=True, message="Project created successfully", data=ProjectResponse.model_validate(project)
    )


@router.get("/{project_id}", response_model=APIResponse[ProjectResponse])
async def get_project(
    project_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Fetch project profile by project ID."""
    project_service = ProjectService(db)
    project = await project_service.get_project(project_id)
    return APIResponse[ProjectResponse](
        success=True, message="Project details resolved successfully", data=ProjectResponse.model_validate(project)
    )


@router.put(
    "/{project_id}",
    response_model=APIResponse[ProjectResponse],
    dependencies=[Depends(PermissionChecker(["project:update"]))],
)
async def update_project(
    project_id: uuid.UUID,
    project_in: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Updates an existing project parameters (requires project:update permission)."""
    project_service = ProjectService(db)
    project = await project_service.update_project(project_id, project_in, current_user.id)
    return APIResponse[ProjectResponse](
        success=True, message="Project updated successfully", data=ProjectResponse.model_validate(project)
    )


@router.delete(
    "/{project_id}", response_model=APIResponse, dependencies=[Depends(PermissionChecker(["project:delete"]))]
)
async def delete_project(
    project_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Flag project as soft deleted and clean up cache keys (requires project:delete permission)."""
    project_service = ProjectService(db)
    await project_service.delete_project(project_id, current_user.id)
    return APIResponse(success=True, message="Project deleted successfully")
