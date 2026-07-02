from datetime import datetime, timezone
from typing import Optional

from app.core.logging import logger
from app.core.redis import redis_client
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.exceptions.custom import ConflictException, UnauthorizedException
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserLogin, UserRegister
from app.schemas.user import UserResponse
from app.services.activity_service import ActivityService
from sqlalchemy.ext.asyncio import AsyncSession


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.role_repo = RoleRepository(db)
        self.activity_service = ActivityService(db)

    async def register(self, user_in: UserRegister):
        """Register a new user, hashes password, and links the Employee role by default."""
        existing_user = await self.user_repo.get_by_email(user_in.email)
        if existing_user:
            raise ConflictException("Email address already registered.")

        # Resolve the default Employee role
        employee_role = await self.role_repo.get_by_name("Employee")
        if not employee_role:
            # Fallback seeder if role table is not seeded
            employee_role = await self.role_repo.create(
                {"name": "Employee", "description": "Default role assigned to staff members."}
            )

        hashed_password = get_password_hash(user_in.password)
        user_data = {
            "email": user_in.email,
            "hashed_password": hashed_password,
            "full_name": user_in.full_name,
            "is_active": True,
        }

        # Create user
        user = await self.user_repo.create(user_data)

        # Link role (many-to-many)
        user.roles.append(employee_role)
        try:
            await self.db.commit()
            await self.db.refresh(user)
        except Exception as e:
            await self.db.rollback()
            raise e

        # Log activity
        await self.activity_service.log_activity(
            user_id=user.id, action="REGISTER", entity_type="USER", entity_id=user.id, details={"email": user.email}
        )

        return user

    async def login(self, user_login: UserLogin) -> dict:
        """Authenticate user email/password, issues tokens, and updates session logging."""
        user = await self.user_repo.get_by_email(user_login.email)
        if not user or not verify_password(user_login.password, user.hashed_password):
            raise UnauthorizedException("Incorrect email or password.")

        if not user.is_active:
            raise UnauthorizedException("This user account is inactive.")

        # Create JWT access and refresh tokens
        access_token = create_access_token(subject=user.id)
        refresh_token = create_refresh_token(subject=user.id)

        # Log authentication activity
        await self.activity_service.log_activity(user_id=user.id, action="LOGIN", entity_type="USER", entity_id=user.id)

        # Return token payload
        user_response = UserResponse.model_validate(user)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user_response,
        }

    async def logout(self, refresh_token: str, access_token: Optional[str] = None) -> None:
        """Blacklists the refresh token (and optionally access token) to log user out."""
        # Blacklist refresh token
        refresh_payload = decode_token(refresh_token)
        if refresh_payload:
            jti = refresh_payload.get("jti")
            exp = refresh_payload.get("exp")
            sub = refresh_payload.get("sub")
            if jti and exp:
                now = datetime.now(timezone.utc).timestamp()
                ttl = int(exp - now)
                if ttl > 0:
                    await redis_client.blacklist_token(jti, ttl)

            # Log activity
            if sub:
                await self.activity_service.log_activity(
                    user_id=sub, action="LOGOUT", entity_type="USER", entity_id=sub
                )

        # Blacklist access token if provided
        if access_token:
            access_payload = decode_token(access_token)
            if access_payload:
                jti = access_payload.get("jti")
                exp = access_payload.get("exp")
                if jti and exp:
                    now = datetime.now(timezone.utc).timestamp()
                    ttl = int(exp - now)
                    if ttl > 0:
                        await redis_client.blacklist_token(jti, ttl)

    async def rotate_tokens(self, refresh_token: str) -> dict:
        """Verifies refresh token, checks blacklist, revokes it, and issues a new pair (Token Rotation)."""
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise UnauthorizedException("Invalid refresh token.")

        jti = payload.get("jti")
        sub = payload.get("sub")
        exp = payload.get("exp")

        if not jti or not sub or not exp:
            raise UnauthorizedException("Invalid token payload structure.")

        # Check if this token is blacklisted in Redis
        is_blacklisted = await redis_client.is_token_blacklisted(jti)
        if is_blacklisted:
            # Revocation replay protection: if an already-used refresh token is submitted, blacklist everything
            logger.warning(f"Replay attack detected for refresh token: {jti}. User: {sub}")
            raise UnauthorizedException("Token has been revoked or blacklisted.")

        # Blacklist the old refresh token so it cannot be used again
        now = datetime.now(timezone.utc).timestamp()
        ttl = int(exp - now)
        if ttl > 0:
            await redis_client.blacklist_token(jti, ttl)

        # Fetch user
        import uuid as uuid_pkg

        try:
            user_uuid = uuid_pkg.UUID(sub)
        except ValueError:
            raise UnauthorizedException("Invalid user ID format in token.")
        user = await self.user_repo.get_with_roles(user_uuid)
        if not user or not user.is_active:
            raise UnauthorizedException("User inactive or deleted.")

        # Generate new token set
        new_access = create_access_token(subject=user.id)
        new_refresh = create_refresh_token(subject=user.id)

        user_response = UserResponse.model_validate(user)
        return {"access_token": new_access, "refresh_token": new_refresh, "token_type": "bearer", "user": user_response}
