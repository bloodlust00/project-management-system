from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.role_repository import RoleRepository
from app.models.role import Role, Permission

class RoleService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.role_repo = RoleRepository(db)

    async def get_roles(self) -> List[Role]:
        """Fetch list of all roles."""
        return await self.role_repo.get_all_roles()

    async def get_permissions(self) -> List[Permission]:
        """Fetch list of all permissions."""
        return await self.role_repo.get_all_permissions()

    async def get_role_by_name(self, name: str) -> Optional[Role]:
        """Fetch role entity mapping by name."""
        return await self.role_repo.get_by_name(name)
