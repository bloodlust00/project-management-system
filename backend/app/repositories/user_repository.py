from typing import Any, List, Optional

from app.models.user import User
from app.repositories.base import BaseRepository
from sqlalchemy import select
from sqlalchemy.orm import selectinload


class UserRepository(BaseRepository[User]):
    def __init__(self, db):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Fetch user by unique email address."""
        query = select(User).filter(User.email == email, User.is_deleted.is_(False))
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_with_roles(self, user_id: Any) -> Optional[User]:
        """Fetch user with roles eagerly loaded."""
        query = select(User).filter(User.id == user_id, User.is_deleted.is_(False)).options(selectinload(User.roles))
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_all_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Fetch active user list with roles eagerly loaded."""
        query = (
            select(User).filter(User.is_deleted.is_(False)).options(selectinload(User.roles)).offset(skip).limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_ids(self, ids: List[Any]) -> List[User]:
        """Fetch multiple user records by their UUIDs in a single query."""
        query = select(User).filter(User.id.in_(ids), User.is_deleted.is_(False))
        result = await self.db.execute(query)
        return list(result.scalars().all())
