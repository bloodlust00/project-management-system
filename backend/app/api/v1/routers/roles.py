from typing import List

from app.dependencies.auth import RoleChecker
from app.dependencies.db import get_db
from app.schemas.common import APIResponse
from app.schemas.role import PermissionResponse, RoleResponse
from app.services.role_service import RoleService
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/rbac", tags=["RBAC & Roles"])


@router.get("/roles", response_model=APIResponse[List[RoleResponse]], dependencies=[Depends(RoleChecker(["Admin"]))])
async def list_roles(db: AsyncSession = Depends(get_db)):
    """Fetch all available user roles (Admin privilege required)."""
    role_service = RoleService(db)
    roles = await role_service.get_roles()
    serialized = [RoleResponse.model_validate(r) for r in roles]
    return APIResponse[List[RoleResponse]](success=True, message="Roles fetched successfully", data=serialized)


@router.get(
    "/permissions", response_model=APIResponse[List[PermissionResponse]], dependencies=[Depends(RoleChecker(["Admin"]))]
)
async def list_permissions(db: AsyncSession = Depends(get_db)):
    """Fetch all registered authorization permissions (Admin privilege required)."""
    role_service = RoleService(db)
    permissions = await role_service.get_permissions()
    serialized = [PermissionResponse.model_validate(p) for p in permissions]
    return APIResponse[List[PermissionResponse]](
        success=True, message="Permissions fetched successfully", data=serialized
    )
