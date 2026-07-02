import uuid
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.db import get_db
from app.dependencies.auth import get_current_user, PermissionChecker
from app.services.comment_service import CommentService
from app.schemas.comment import CommentCreate, CommentResponse
from app.schemas.common import APIResponse
from app.models.user import User
from app.exceptions.custom import ForbiddenException

router = APIRouter(prefix="/comments", tags=["Comments"])

@router.get("/task/{task_id}", response_model=APIResponse[List[CommentResponse]])
async def get_task_comments(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch all comments posted in a task thread."""
    comment_service = CommentService(db)
    comments = await comment_service.get_task_comments(task_id)
    serialized = [CommentResponse.model_validate(c) for c in comments]
    return APIResponse[List[CommentResponse]](
        success=True,
        message="Comments fetched successfully",
        data=serialized
    )

@router.post("/task/{task_id}", response_model=APIResponse[CommentResponse], dependencies=[Depends(PermissionChecker(["comment:create"]))])
async def create_comment(
    task_id: uuid.UUID,
    comment_in: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new comment in a task thread."""
    comment_service = CommentService(db)
    comment = await comment_service.create_comment(task_id, comment_in, current_user.id)
    return APIResponse[CommentResponse](
        success=True,
        message="Comment added successfully",
        data=CommentResponse.model_validate(comment)
    )

@router.delete("/{comment_id}", response_model=APIResponse, dependencies=[Depends(PermissionChecker(["comment:delete"]))])
async def delete_comment(
    comment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deletes a comment (Employees can only delete comments they authored, Managers/Admins can delete any comment)."""
    comment_service = CommentService(db)
    comment = await comment_service.get_comment(comment_id)
    
    # Resolve roles
    user_roles = [r.name for r in current_user.roles]
    is_admin_or_manager = "Admin" in user_roles or "Manager" in user_roles

    if not is_admin_or_manager and comment.author_id != current_user.id:
        raise ForbiddenException("Access Denied. You can only delete your own comments.")

    await comment_service.delete_comment(comment_id, current_user.id)
    return APIResponse(
        success=True,
        message="Comment deleted successfully"
    )
