import time
import uuid
from typing import Optional

from app.core.logging import logger
from app.core.redis import redis_client
from app.dependencies.auth import PermissionChecker, get_current_user
from app.dependencies.db import get_db
from app.models.comment import Comment
from app.models.project import Project
from app.models.task import Task, TaskPriority, TaskStatus
from app.models.user import User
from app.schemas.activity import ActivityLogResponse
from app.schemas.common import APIResponse, PaginatedData, PaginationMeta
from app.services.activity_service import ActivityService
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/metrics", tags=["Metrics & Health"])


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Liveness check to verify the API server is up and responsive."""
    return {"status": "healthy", "timestamp": time.time()}


@router.get("/ready")
async def ready_check(db: AsyncSession = Depends(get_db)):
    """Readiness check verifying database and cache channels are fully active."""
    db_ok = False
    try:
        await db.execute(select(1))
        db_ok = True
    except Exception as e:
        logger.error(f"Readiness check database ping failed: {e}")

    redis_ok = await redis_client.is_active()

    status_code = status.HTTP_200_OK if db_ok and redis_ok else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content={
            "success": db_ok and redis_ok,
            "message": "System ready" if db_ok and redis_ok else "System components degraded",
            "data": {
                "database": "connected" if db_ok else "disconnected",
                "redis": "connected" if redis_ok else "disconnected",
            },
            "meta": {"timestamp": time.time()},
        },
    )


@router.get("/version")
async def version_check():
    """Version check returning deployment tag parameters."""
    return {
        "success": True,
        "message": "Version retrieved",
        "data": {"version": "1.0.0", "environment": "production", "release_tag": "v1.0.0-prod"},
        "meta": {"timestamp": time.time()},
    }


@router.get("/metrics", dependencies=[Depends(PermissionChecker(["audit:read"]))])
async def metrics_check(db: AsyncSession = Depends(get_db)):
    """System metrics diagnostic logs summary (JSON format). Requires audit:read permission."""
    try:
        # Resolve active database entity totals
        proj_count = await db.execute(select(func.count(Project.id)).filter(Project.is_deleted.is_(False)))
        task_count = await db.execute(select(func.count(Task.id)).filter(Task.is_deleted.is_(False)))
        user_count = await db.execute(select(func.count(User.id)).filter(User.is_deleted.is_(False)))

        return {
            "success": True,
            "message": "Metrics calculated",
            "data": {
                "active_projects": proj_count.scalar() or 0,
                "active_tasks": task_count.scalar() or 0,
                "active_users": user_count.scalar() or 0,
                "cache_connected": await redis_client.is_active(),
            },
            "meta": {"timestamp": time.time()},
        }
    except Exception as e:
        logger.error(f"Failed to fetch system metrics: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "Failed to compile metrics",
                "errors": [{"message": str(e)}],
                "meta": {"timestamp": time.time()},
            },
        )


@router.get("/stats", response_model=APIResponse)
async def dashboard_stats(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Retrieves high-level analytics for the dashboard (leverages Redis caching)."""
    cache_key = "dashboard:stats"

    # Check cache
    cached_stats = await redis_client.get_cache(cache_key)
    if cached_stats:
        return APIResponse(
            success=True,
            message="Dashboard statistics fetched from cache",
            data=cached_stats,
            meta={"cached": True, "timestamp": time.time()},
        )

    # Cache miss - compute statistics
    # Projects count
    proj_query = select(func.count(Project.id)).filter(Project.is_deleted.is_(False))
    proj_result = await db.execute(proj_query)
    total_projects = proj_result.scalar() or 0

    # Tasks counts by status
    status_stats = {}
    for task_status in TaskStatus:
        t_query = select(func.count(Task.id)).filter(Task.status == task_status, Task.is_deleted.is_(False))
        t_result = await db.execute(t_query)
        status_stats[task_status.value] = t_result.scalar() or 0

    # Total tasks
    total_tasks = sum(status_stats.values())

    # Task priority distribution
    priority_stats = {}
    for prio in TaskPriority:
        p_query = select(func.count(Task.id)).filter(Task.priority == prio, Task.is_deleted.is_(False))
        p_result = await db.execute(p_query)
        priority_stats[prio.value] = p_result.scalar() or 0

    # Comments count
    com_query = select(func.count(Comment.id)).filter(Comment.is_deleted.is_(False))
    com_result = await db.execute(com_query)
    total_comments = com_result.scalar() or 0

    stats_data = {
        "total_projects": total_projects,
        "total_tasks": total_tasks,
        "total_comments": total_comments,
        "tasks_by_status": status_stats,
        "tasks_by_priority": priority_stats,
    }

    # Write to Redis for 5 minutes
    await redis_client.set_cache(cache_key, stats_data, expire_seconds=300)

    return APIResponse(
        success=True,
        message="Dashboard statistics calculated",
        data=stats_data,
        meta={"cached": False, "timestamp": time.time()},
    )


@router.get(
    "/audit-logs",
    response_model=APIResponse[PaginatedData[ActivityLogResponse]],
    dependencies=[Depends(PermissionChecker(["audit:read"]))],
)
async def list_audit_logs(
    user_id: Optional[uuid.UUID] = Query(None),
    entity_type: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """Fetch system-wide operations audit trails (requires audit:read permission)."""
    activity_service = ActivityService(db)
    logs, total = await activity_service.get_logs(
        user_id=user_id, entity_type=entity_type, action=action, skip=skip, limit=limit
    )

    pages = (total + limit - 1) // limit if limit > 0 else 0
    serialized = [ActivityLogResponse.model_validate(log) for log in logs]

    return APIResponse[PaginatedData[ActivityLogResponse]](
        success=True,
        message="Audit logs fetched successfully",
        data=PaginatedData(
            items=serialized, pagination=PaginationMeta(total=total, page=(skip // limit) + 1, size=limit, pages=pages)
        ),
        meta={"timestamp": time.time()},
    )
