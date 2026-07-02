from typing import AsyncGenerator

import pytest
from app.core.database import Base
from app.core.redis import redis_client
from app.dependencies.db import get_db
from app.dependencies.redis import get_redis
from app.main import app
from app.models.role import Permission, Role
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# In-memory async SQLite engine for testing
DATABASE_URL_TEST = "sqlite+aiosqlite:///:memory:"

engine_test = create_async_engine(DATABASE_URL_TEST, connect_args={"check_same_thread": False})

AsyncSessionLocalTest = async_sessionmaker(bind=engine_test, class_=AsyncSession, expire_on_commit=False)


# Mock Redis Client class
class MockRedisClient:
    def __init__(self):
        self.store = {}

    async def is_active(self) -> bool:
        return True

    async def blacklist_token(self, token_jti: str, expires_in_seconds: int) -> bool:
        self.store[f"blacklist:{token_jti}"] = "true"
        return True

    async def is_token_blacklisted(self, token_jti: str) -> bool:
        return f"blacklist:{token_jti}" in self.store

    async def get_cache(self, key: str):
        return self.store.get(key)

    async def set_cache(self, key: str, value: any, expire_seconds: int = 300):
        self.store[key] = value
        return True

    async def delete_cache(self, key: str):
        self.store.pop(key, None)
        return True

    async def delete_by_pattern(self, pattern: str):
        # simple check
        keys_to_del = [k for k in self.store.keys() if k.startswith(pattern.replace("*", ""))]
        for k in keys_to_del:
            self.store.pop(k, None)
        return True


mock_redis = MockRedisClient()

# Patch global redis_client instance in place to prevent network calls during testing
redis_client.is_active = mock_redis.is_active
redis_client.blacklist_token = mock_redis.blacklist_token
redis_client.is_token_blacklisted = mock_redis.is_token_blacklisted
redis_client.get_cache = mock_redis.get_cache
redis_client.set_cache = mock_redis.set_cache
redis_client.delete_cache = mock_redis.delete_cache
redis_client.delete_by_pattern = mock_redis.delete_by_pattern


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session", autouse=True)
async def init_test_db():
    """Initializes in-memory database and creates tables."""
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Generates an independent test database session for each test run with transaction rollback isolation."""
    connection = await engine_test.connect()
    transaction = await connection.begin()

    # Bind session to connection
    session = AsyncSession(bind=connection, expire_on_commit=False)

    from app.utils.seeder import PERMISSIONS, ROLE_PERMISSIONS_MAPPING

    # Seed Permissions
    permissions_map = {}
    for perm_data in PERMISSIONS:
        perm = Permission(**perm_data)
        session.add(perm)
        permissions_map[perm_data["code"]] = perm
    await session.flush()

    # Seed Roles
    roles_map = {}
    for role_name, perm_codes in ROLE_PERMISSIONS_MAPPING.items():
        role = Role(name=role_name, description=f"Test {role_name}")
        session.add(role)
        for code in perm_codes:
            role.permissions.append(permissions_map[code])
        roles_map[role_name] = role
    await session.flush()

    yield session

    await session.close()
    await transaction.rollback()
    await connection.close()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """FastAPI test HTTP client with overridden dependencies."""

    def override_get_db():
        return db_session

    def override_get_redis():
        return mock_redis

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
