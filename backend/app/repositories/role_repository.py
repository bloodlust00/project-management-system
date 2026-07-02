from typing import List, Optional

from app.models.role import Permission, Role
from app.repositories.base import BaseRepository
from sqlalchemy import select


class RoleRepository(BaseRepository[Role]):
    def __init__(self, db):
        super().__init__(Role, db)

    async def get_by_name(self, name: str) -> Optional[Role]:
        """Fetch role by name."""
        query = select(Role).filter(Role.name == name)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_all_roles(self) -> List[Role]:
        """Fetch list of all roles."""
        query = select(Role)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # Permission helper operations
    async def get_permission_by_code(self, code: str) -> Optional[Permission]:
        """Fetch permission by action code (e.g. project:create)."""
        query = select(Permission).filter(Permission.code == code)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def create_permission(self, name: str, code: str, description: Optional[str] = None) -> Permission:
        """Create a new permission entry."""
        permission = Permission(name=name, code=code, description=description)
        self.db.add(permission)
        try:
            await self.db.commit()
            await self.db.refresh(permission)
            return permission
        except Exception as e:
            await self.db.rollback()
            raise e

    async def get_all_permissions(self) -> List[Permission]:
        """Fetch list of all system permissions."""
        query = select(Permission)
        result = await self.db.execute(query)
        return list(result.scalars().all())
