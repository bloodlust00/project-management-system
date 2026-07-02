from typing import List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_repository import UserRepository
from app.repositories.role_repository import RoleRepository
from app.services.activity_service import ActivityService
from app.exceptions.custom import NotFoundException, BadRequestException
from app.schemas.user import UserUpdate, UserCreate
from app.models.user import User
from app.core.security import get_password_hash

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.role_repo = RoleRepository(db)
        self.activity_service = ActivityService(db)

    async def get_user(self, user_id: Any) -> User:
        """Fetch user by primary key, raising NotFound if missing."""
        user = await self.user_repo.get_with_roles(user_id)
        if not user:
            raise NotFoundException("User account not found.")
        return user

    async def get_all_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Fetch list of all active user records."""
        return await self.user_repo.get_all_active_users(skip=skip, limit=limit)

    async def update_user(self, user_id: Any, user_in: UserUpdate, current_user_id: Any) -> User:
        """Update user record details, hashing password if altered, and log audit actions."""
        user = await self.get_user(user_id)
        
        # Format updates map
        update_data = user_in.model_dump(exclude_unset=True)
        if "password" in update_data and update_data["password"]:
            update_data["hashed_password"] = get_password_hash(update_data["password"])
            del update_data["password"]

        updated_user = await self.user_repo.update(db_obj=user, obj_in=update_data)

        # Log details
        await self.activity_service.log_activity(
            user_id=current_user_id,
            action="UPDATE",
            entity_type="USER",
            entity_id=user.id,
            details={"updated_fields": list(update_data.keys())}
        )
        return updated_user

    async def update_user_roles(self, user_id: Any, role_names: List[str], current_user_id: Any) -> User:
        """Modifies user role assignments, restricted to Administrative roles."""
        user = await self.get_user(user_id)
        
        # Clear existing roles
        user.roles.clear()
        
        # Resolve and append new roles
        for role_name in role_names:
            role = await self.role_repo.get_by_name(role_name)
            if not role:
                raise NotFoundException(f"Role '{role_name}' does not exist.")
            user.roles.append(role)
        try:
            await self.db.commit()
            await self.db.refresh(user)
        except Exception as e:
            await self.db.rollback()
            raise e

        # Log role modifications
        await self.activity_service.log_activity(
            user_id=current_user_id,
            action="UPDATE_ROLES",
            entity_type="USER",
            entity_id=user.id,
            details={"assigned_roles": role_names}
        )
        return user

    async def delete_user(self, user_id: Any, current_user_id: Any) -> User:
        """Flag user as soft deleted, locking credentials and active states."""
        user = await self.get_user(user_id)
        
        user.is_active = False
        await self.user_repo.remove(id=user_id)
        
        # Log deletion action
        await self.activity_service.log_activity(
            user_id=current_user_id,
            action="DELETE",
            entity_type="USER",
            entity_id=user_id
        )
        return user
