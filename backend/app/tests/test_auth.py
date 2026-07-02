import pytest
from app.models.user import User
from httpx import AsyncClient
from sqlalchemy import select


@pytest.mark.anyio
async def test_register_user_success(client: AsyncClient, db_session):
    """Test successful user registration flow."""
    payload = {"email": "testuser@example.com", "password": "Password123!", "full_name": "Test Employee"}

    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["success"] is True
    assert data["data"]["user"]["email"] == "testuser@example.com"

    # Verify in DB
    result = await db_session.execute(select(User).filter(User.email == "testuser@example.com"))
    user = result.scalars().first()
    assert user is not None
    assert user.full_name == "Test Employee"


@pytest.mark.anyio
async def test_register_user_weak_password(client: AsyncClient):
    """Test registration block on weak passwords."""
    payload = {"email": "weak@example.com", "password": "simple", "full_name": "Weak User"}

    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400

    data = response.json()
    assert data["success"] is False
    assert "password" in data["message"].lower() or any("password" in err["field"].lower() for err in data["errors"])


@pytest.mark.anyio
async def test_login_user_success(client: AsyncClient):
    """Test successful login and JWT generation."""
    # First register user
    register_payload = {"email": "login@example.com", "password": "Password123!", "full_name": "Login User"}
    await client.post("/api/v1/auth/register", json=register_payload)

    # Attempt Login
    login_payload = {"email": "login@example.com", "password": "Password123!"}
    response = await client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]
    assert data["data"]["user"]["email"] == "login@example.com"


@pytest.mark.anyio
async def test_token_refresh_rotation(client: AsyncClient):
    """Test token refresh rotation capability."""
    # Register and Login
    email = "refresh@example.com"
    await client.post(
        "/api/v1/auth/register", json={"email": email, "password": "Password123!", "full_name": "Refresh User"}
    )

    login_res = await client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    tokens = login_res.json()["data"]
    refresh_token = tokens["refresh_token"]

    # Rotate Refresh Token
    refresh_res = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_res.status_code == 200

    data = refresh_res.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert data["data"]["access_token"] != tokens["access_token"]
