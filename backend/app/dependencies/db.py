from typing import AsyncGenerator

from app.core.database import AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency generating async database sessions with automatic close handles."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
