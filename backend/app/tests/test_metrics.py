import pytest
from app.core.security import get_password_hash
from app.models.role import Role
from app.models.user import User
from httpx import AsyncClient
from sqlalchemy import select


async def create_user_with_role(db_session, email: str, role_name: str) -> User:
    """Helper to register users with designated system role configurations."""
    result = await db_session.execute(select(Role).filter(Role.name == role_name))
    role = result.scalars().first()

    hashed_pw = get_password_hash("Password123!")
    user = User(email=email, hashed_password=hashed_pw, full_name=f"Test {role_name}", is_active=True)
    db_session.add(user)
    user.roles.append(role)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.anyio
async def test_health_check(client: AsyncClient):
    """Test health check returns 200 and healthy status."""
    response = await client.get("/api/v1/metrics/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.anyio
async def test_ready_check(client: AsyncClient):
    """Test readiness check pings database and cache successfully."""
    response = await client.get("/api/v1/metrics/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "database" in data["data"]
    assert "redis" in data["data"]


@pytest.mark.anyio
async def test_version_check(client: AsyncClient):
    """Test version endpoint returns application details."""
    response = await client.get("/api/v1/metrics/version")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["version"] == "1.0.0"


@pytest.mark.anyio
async def test_metrics_check(client: AsyncClient, db_session):
    """Test metrics endpoint returns active resource numbers."""
    await create_user_with_role(db_session, "metrics_manager@example.com", "Manager")

    login_res = await client.post(
        "/api/v1/auth/login", json={"email": "metrics_manager@example.com", "password": "Password123!"}
    )
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/v1/metrics/metrics", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "active_projects" in data["data"]
    assert "active_tasks" in data["data"]
    assert "active_users" in data["data"]
