import asyncio
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import AsyncSessionLocal, Base, engine
from app.core.security import get_password_hash
from app.core.config import settings
from app.models import Role, Permission, User
from app.core.logging import logger, setup_logging

# Configure logging before running seeder standalone
setup_logging()

# Definitions of default permissions
PERMISSIONS = [
    {"name": "Create Projects", "code": "project:create", "description": "Allows creating new projects."},
    {"name": "Read Projects", "code": "project:read", "description": "Allows reading project details."},
    {"name": "Update Projects", "code": "project:update", "description": "Allows updating project details."},
    {"name": "Delete Projects", "code": "project:delete", "description": "Allows deleting projects."},
    {"name": "Create Tasks", "code": "task:create", "description": "Allows creating tasks within projects."},
    {"name": "Read Tasks", "code": "task:read", "description": "Allows reading task details."},
    {"name": "Update Tasks", "code": "task:update", "description": "Allows editing task details."},
    {"name": "Delete Tasks", "code": "task:delete", "description": "Allows deleting tasks."},
    {"name": "Create Comments", "code": "comment:create", "description": "Allows commenting on tasks."},
    {"name": "Delete Comments", "code": "comment:delete", "description": "Allows deleting comments."},
    {"name": "Manage Users", "code": "user:manage", "description": "Allows managing user accounts and roles."},
    {"name": "Read Audit Logs", "code": "audit:read", "description": "Allows viewing application audit and activity logs."},
]

# Definitions of default roles and their associated permission codes
ROLE_PERMISSIONS_MAPPING = {
    "Admin": [
        "project:create", "project:read", "project:update", "project:delete",
        "task:create", "task:read", "task:update", "task:delete",
        "comment:create", "comment:delete",
        "user:manage",
        "audit:read"
    ],
    "Manager": [
        "project:create", "project:read", "project:update",
        "task:create", "task:read", "task:update", "task:delete",
        "comment:create", "comment:delete",
        "audit:read"
    ],
    "Employee": [
        "project:read",
        "task:read", "task:update",
        "comment:create"
    ]
}

async def seed_data():
    """Executes database seeding for Roles, Permissions, and Initial Admin account."""
    async with AsyncSessionLocal() as db:
        logger.info("Starting database seeding...")

        # 1. Seed Permissions
        permissions_map = {}
        for perm_data in PERMISSIONS:
            query = select(Permission).filter(Permission.code == perm_data["code"])
            result = await db.execute(query)
            existing_perm = result.scalars().first()

            if not existing_perm:
                perm = Permission(**perm_data)
                db.add(perm)
                logger.info(f"Seeding Permission: {perm_data['code']}")
                permissions_map[perm_data["code"]] = perm
            else:
                permissions_map[perm_data["code"]] = existing_perm

        await db.commit()

        # 2. Seed Roles and map permissions
        roles_map = {}
        for role_name, perm_codes in ROLE_PERMISSIONS_MAPPING.items():
            query = select(Role).filter(Role.name == role_name).options(selectinload(Role.permissions))
            result = await db.execute(query)
            existing_role = result.scalars().first()

            if not existing_role:
                role = Role(name=role_name, description=f"Default {role_name} access role.")
                db.add(role)
                logger.info(f"Seeding Role: {role_name}")
            else:
                role = existing_role

            # Map permissions
            role.permissions.clear()
            for code in perm_codes:
                if code in permissions_map:
                    role.permissions.append(permissions_map[code])
            
            roles_map[role_name] = role

        await db.commit()

        # 3. Seed Initial Administrator User
        query = select(User).filter(User.email == settings.INITIAL_ADMIN_EMAIL)
        result = await db.execute(query)
        existing_admin = result.scalars().first()

        if not existing_admin:
            hashed_pw = get_password_hash(settings.INITIAL_ADMIN_PASSWORD)
            admin_user = User(
                email=settings.INITIAL_ADMIN_EMAIL,
                hashed_password=hashed_pw,
                full_name="System Administrator",
                is_active=True
            )
            db.add(admin_user)
            admin_user.roles.append(roles_map["Admin"])
            logger.info(f"Seeding Administrator User: {settings.INITIAL_ADMIN_EMAIL}")
        else:
            logger.info(f"Administrator User '{settings.INITIAL_ADMIN_EMAIL}' already exists.")

        await db.commit()
        logger.info("Database seeding successfully completed.")

if __name__ == "__main__":
    asyncio.run(seed_data())
