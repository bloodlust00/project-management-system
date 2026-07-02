from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from app.core.database import Base
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get(self, id: Any) -> Optional[ModelType]:
        """Fetch a single record by primary key, filtering out soft-deleted items."""
        query = select(self.model).filter(self.model.id == id)
        if hasattr(self.model, "is_deleted"):
            query = query.filter(self.model.is_deleted.is_(False))

        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_multi(
        self, *, skip: int = 0, limit: int = 100, sort_by: str = "created_at", sort_order: str = "desc"
    ) -> List[ModelType]:
        """Fetch multiple records with pagination and sorting."""
        query = select(self.model)
        if hasattr(self.model, "is_deleted"):
            query = query.filter(self.model.is_deleted.is_(False))

        # Apply sorting
        if hasattr(self.model, sort_by):
            sort_attr = getattr(self.model, sort_by)
            if sort_order.lower() == "desc":
                query = query.order_by(sort_attr.desc())
            else:
                query = query.order_by(sort_attr.asc())
        else:
            if hasattr(self.model, "created_at"):
                query = query.order_by(self.model.created_at.desc())

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count(self) -> int:
        """Count active records."""
        query = select(func.count()).select_from(self.model)
        if hasattr(self.model, "is_deleted"):
            query = query.filter(self.model.is_deleted.is_(False))
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def create(self, obj_in_data: Dict[str, Any]) -> ModelType:
        """Instantiate and commit a new model record."""
        db_obj = self.model(**obj_in_data)
        self.db.add(db_obj)
        try:
            await self.db.commit()
            await self.db.refresh(db_obj)
            return db_obj
        except Exception as e:
            await self.db.rollback()
            raise e

    async def update(self, *, db_obj: ModelType, obj_in: Dict[str, Any]) -> ModelType:
        """Update an existing model record with dynamic parameters."""
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        self.db.add(db_obj)
        try:
            await self.db.commit()
            await self.db.refresh(db_obj)
            return db_obj
        except Exception as e:
            await self.db.rollback()
            raise e

    async def remove(self, *, id: Any, force_hard_delete: bool = False) -> Optional[ModelType]:
        """Removes a record using a soft-delete mechanism by default, or forces a hard delete."""
        query = select(self.model).filter(self.model.id == id)
        result = await self.db.execute(query)
        db_obj = result.scalars().first()

        if not db_obj:
            return None

        try:
            if hasattr(self.model, "is_deleted") and not force_hard_delete:
                setattr(db_obj, "is_deleted", True)
                self.db.add(db_obj)
                await self.db.commit()
                await self.db.refresh(db_obj)
            else:
                await self.db.delete(db_obj)
                await self.db.commit()
            return db_obj
        except Exception as e:
            await self.db.rollback()
            raise e
