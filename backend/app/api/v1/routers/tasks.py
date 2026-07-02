import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.db import get_db
from app.dependencies.auth import get_current_user, PermissionChecker, RoleChecker
from app.services.task_service import TaskService
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.schemas.common import APIResponse, PaginatedData, PaginationMeta
from app.models.user import User
from app.models.task import TaskStatus, TaskPriority
from app.exceptions.custom import ForbiddenException

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.get("/", response_model=APIResponse[PaginatedData[TaskResponse]])
async def list_tasks(
    project_id: Optional[uuid.UUID] = Query(None),
    status: Optional[TaskStatus] = Query(None),
    priority: Optional[TaskPriority] = Query(None),
    search: Optional[str] = Query(None),
    assignee_id: Optional[uuid.UUID] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=1000),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch tasks list matching filters, status, assignees, or project ID."""
    task_service = TaskService(db)
    tasks, total = await task_service.get_tasks(
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

    pages = (total + limit - 1) // limit if limit > 0 else 0
    serialized = [TaskResponse.model_validate(t) for t in tasks]

    return APIResponse[PaginatedData[TaskResponse]](
        success=True,
        message="Tasks list fetched successfully",
        data=PaginatedData(
            items=serialized,
            pagination=PaginationMeta(
                total=total,
                page=(skip // limit) + 1,
                size=limit,
                pages=pages
            )
        )
    )

@router.post("/project/{project_id}", response_model=APIResponse[TaskResponse], dependencies=[Depends(PermissionChecker(["task:create"]))])
async def create_task(
    project_id: uuid.UUID,
    task_in: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Creates a new task in a project (Manager/Admin privilege required)."""
    task_service = TaskService(db)
    task = await task_service.create_task(project_id, task_in, current_user.id)
    return APIResponse[TaskResponse](
        success=True,
        message="Task created successfully",
        data=TaskResponse.model_validate(task)
    )

@router.get("/{task_id}", response_model=APIResponse[TaskResponse])
async def get_task_details(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch task details matching task ID."""
    task_service = TaskService(db)
    task = await task_service.get_task(task_id)
    return APIResponse[TaskResponse](
        success=True,
        message="Task details resolved successfully",
        data=TaskResponse.model_validate(task)
    )

@router.put("/{task_id}", response_model=APIResponse[TaskResponse])
async def update_task(
    task_id: uuid.UUID,
    task_in: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Updates task parameters (Enforces Employee role assignment and status-only restriction)."""
    task_service = TaskService(db)
    task = await task_service.get_task(task_id)
    
    # Resolve role context
    user_roles = [r.name for r in current_user.roles]
    is_admin_or_manager = "Admin" in user_roles or "Manager" in user_roles

    if not is_admin_or_manager:
        # Enforce Employee constraints:
        # 1. Must be assigned to this task
        assignee_ids = [u.id for u in task.assignees]
        if current_user.id not in assignee_ids:
            raise ForbiddenException("Access Denied. You are not assigned to this task.")
        
        # 2. Can ONLY update status
        update_fields = task_in.model_dump(exclude_unset=True)
        if any(key != "status" for key in update_fields.keys()):
            raise ForbiddenException("Access Denied. Employees can only update the status of assigned tasks.")

    updated_task = await task_service.update_task(task_id, task_in, current_user.id)
    return APIResponse[TaskResponse](
        success=True,
        message="Task updated successfully",
        data=TaskResponse.model_validate(updated_task)
    )

@router.delete("/{task_id}", response_model=APIResponse, dependencies=[Depends(PermissionChecker(["task:delete"]))])
async def delete_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Flag task as soft-deleted (requires task:delete permission)."""
    task_service = TaskService(db)
    await task_service.delete_task(task_id, current_user.id)
    return APIResponse(
        success=True,
        message="Task deleted successfully"
    )

@router.get("/export/csv", dependencies=[Depends(PermissionChecker(["audit:read"]))])
async def export_tasks_csv(
    project_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Exports tasks into a CSV file (requires audit:read permission)."""
    task_service = TaskService(db)
    csv_data = await task_service.export_tasks_to_csv(project_id)
    
    response = Response(content=csv_data, media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=tasks_export.csv"
    return response
