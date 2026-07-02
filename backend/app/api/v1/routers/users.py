import uuid
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.db import get_db
from app.dependencies.auth import get_current_user, RoleChecker, PermissionChecker
from app.services.user_service import UserService
from app.schemas.user import UserResponse, UserUpdate, UserUpdateRoles
from app.schemas.common import APIResponse, PaginatedData, PaginationMeta
from app.models.user import User

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=APIResponse[UserResponse])
async def get_me(current_user: User = Depends(get_current_user)):
    """Fetch active profile information for currently authenticated user."""
    return APIResponse[UserResponse](
        success=True,
        message="Profile details fetched successfully",
        data=UserResponse.model_validate(current_user)
    )

@router.put("/me", response_model=APIResponse[UserResponse])
async def update_me(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Allows current user to edit their personal profile fields."""
    user_service = UserService(db)
    updated_user = await user_service.update_user(
        user_id=current_user.id,
        user_in=user_in,
        current_user_id=current_user.id
    )
    return APIResponse[UserResponse](
        success=True,
        message="Profile details updated successfully",
        data=UserResponse.model_validate(updated_user)
    )

@router.get("/", response_model=APIResponse[PaginatedData[UserResponse]], dependencies=[Depends(RoleChecker(["Admin"]))])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List active user accounts (Admin privilege required)."""
    user_service = UserService(db)
    users = await user_service.get_all_users(skip=skip, limit=limit)
    
    # Calculate count
    from app.repositories.user_repository import UserRepository
    user_repo = UserRepository(db)
    total = await user_repo.count()
    
    pages = (total + limit - 1) // limit if limit > 0 else 0
    serialized = [UserResponse.model_validate(u) for u in users]
    
    return APIResponse(
        success=True,
        message="Users list fetched successfully",
        data=PaginatedData(
            items=serialized,
            pagination=PaginationMeta(
                total=total,
                page=(skip // limit) + 1 if limit > 0 else 1,
                size=limit,
                pages=pages
            )
        )
    )

@router.get("/{user_id}", response_model=APIResponse[UserResponse])
async def get_user_by_id(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Fetch profile data by user ID (Admin only, or self querying)."""
    # Enforce access boundary
    is_admin = any(r.name == "Admin" for r in current_user.roles)
    if not is_admin and current_user.id != user_id:
        from app.exceptions.custom import ForbiddenException
        raise ForbiddenException("Access denied. You can only view your own profile.")

    user_service = UserService(db)
    user = await user_service.get_user(user_id)
    return APIResponse[UserResponse](
        success=True,
        message="User profile resolved successfully",
        data=UserResponse.model_validate(user)
    )

@router.put("/{user_id}/roles", response_model=APIResponse[UserResponse], dependencies=[Depends(RoleChecker(["Admin"]))])
async def update_user_roles(
    user_id: uuid.UUID,
    roles_in: UserUpdateRoles,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Updates user roles mapping (Admin privilege required)."""
    user_service = UserService(db)
    updated_user = await user_service.update_user_roles(
        user_id=user_id,
        role_names=roles_in.role_names,
        current_user_id=current_user.id
    )
    return APIResponse[UserResponse](
        success=True,
        message="User roles updated successfully",
        data=UserResponse.model_validate(updated_user)
    )

@router.delete("/{user_id}", response_model=APIResponse, dependencies=[Depends(RoleChecker(["Admin"]))])
async def delete_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Soft delete user account from application access (Admin privilege required)."""
    user_service = UserService(db)
    await user_service.delete_user(user_id=user_id, current_user_id=current_user.id)
    return APIResponse(
        success=True,
        message="User account deleted successfully."
    )
