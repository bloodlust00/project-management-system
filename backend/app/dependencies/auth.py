from typing import List

from app.core.config import settings
from app.core.redis import redis_client
from app.core.security import decode_token
from app.dependencies.db import get_db
from app.exceptions.custom import ForbiddenException, UnauthorizedException
from app.models.user import User
from app.repositories.user_repository import UserRepository
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

# Define the OAuth2 bearer scheme pointing to login route
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


async def get_current_user(db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    """FastAPI dependency resolving current user context from JWT token."""
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise UnauthorizedException("Could not validate credentials.")

    jti = payload.get("jti")
    user_id = payload.get("sub")

    if not jti or not user_id:
        raise UnauthorizedException("Could not validate credentials.")

    # Enforce Redis blacklisting lookup
    is_blacklisted = await redis_client.is_token_blacklisted(jti)
    if is_blacklisted:
        raise UnauthorizedException("Token is invalid or blacklisted.")

    import uuid as uuid_pkg

    try:
        user_uuid = uuid_pkg.UUID(user_id)
    except ValueError:
        raise UnauthorizedException("Invalid user ID format in token.")

    user_repo = UserRepository(db)
    user = await user_repo.get_with_roles(user_uuid)
    if not user:
        raise UnauthorizedException("User not found.")

    if not user.is_active:
        raise UnauthorizedException("User account is disabled.")

    return user


class PermissionChecker:
    def __init__(self, allowed_permissions: List[str]):
        self.allowed_permissions = allowed_permissions

    def __call__(self, current_user: User = Depends(get_current_user)) -> None:
        """Call method verifying if the user holds required permissions or Admin rights."""
        # Admin bypasses all checks
        user_role_names = [role.name for role in current_user.roles]
        if "Admin" in user_role_names:
            return

        # Build list of permissions user holds
        user_permission_codes = set()
        for role in current_user.roles:
            for permission in role.permissions:
                user_permission_codes.add(permission.code)

        # Check intersection
        has_permission = any(perm in user_permission_codes for perm in self.allowed_permissions)
        if not has_permission:
            raise ForbiddenException("Permission denied. Insufficient access rights.")


class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> None:
        """Call method verifying if user belongs to one of allowed roles."""
        user_role_names = [role.name for role in current_user.roles]
        # Admin bypasses roles checks
        if "Admin" in user_role_names:
            return

        has_role = any(role in user_role_names for role in self.allowed_roles)
        if not has_role:
            raise ForbiddenException("Permission denied. Insufficient role permissions.")
