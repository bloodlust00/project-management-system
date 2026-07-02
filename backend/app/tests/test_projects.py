import pytest
from app.core.security import get_password_hash
from app.models.role import Role
from app.models.user import User
from httpx import AsyncClient
from sqlalchemy import select


async def create_user_with_role(db_session, email: str, role_name: str) -> User:
    """Helper to register users with designated system role configurations."""
    # Resolve role
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
async def test_manager_can_create_project(client: AsyncClient, db_session):
    """Verify that a user with Manager role can create projects."""
    await create_user_with_role(db_session, "manager@example.com", "Manager")

    # Login to obtain token
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "manager@example.com", "password": "Password123!"},  # matches pre-calculated hash mock
    )
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create project
    proj_payload = {"name": "Manager Project", "description": "Created by test manager."}

    response = await client.post("/api/v1/projects/", json=proj_payload, headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["data"]["name"] == "Manager Project"


@pytest.mark.anyio
async def test_employee_blocked_from_deleting_projects(client: AsyncClient, db_session):
    """Verify that a user with Employee role is denied permission to delete projects."""
    await create_user_with_role(db_session, "employee@example.com", "Employee")
    await create_user_with_role(db_session, "project_owner@example.com", "Manager")

    # Create project first as Manager
    login_mgr = await client.post(
        "/api/v1/auth/login", json={"email": "project_owner@example.com", "password": "Password123!"}
    )
    mgr_token = login_mgr.json()["data"]["access_token"]

    response_proj = await client.post(
        "/api/v1/projects/", json={"name": "Delete Test Project"}, headers={"Authorization": f"Bearer {mgr_token}"}
    )
    project_id = response_proj.json()["data"]["id"]

    # Attempt to delete project as Employee
    login_emp = await client.post(
        "/api/v1/auth/login", json={"email": "employee@example.com", "password": "Password123!"}
    )
    emp_token = login_emp.json()["data"]["access_token"]

    # Delete attempt
    response_delete = await client.delete(
        f"/api/v1/projects/{project_id}", headers={"Authorization": f"Bearer {emp_token}"}
    )
    # Enforces 403 Forbidden for Employee roles
    assert response_delete.status_code == 403
    assert response_delete.json()["success"] is False
