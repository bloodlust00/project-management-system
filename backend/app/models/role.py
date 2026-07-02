from typing import List
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import BaseModelMixin
from app.models.association import role_permissions

class Permission(Base, BaseModelMixin):
    __tablename__ = "permissions"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True) # e.g. "project:create"
    description: Mapped[str] = mapped_column(String(255), nullable=True)

    # Relationships
    roles: Mapped[List["Role"]] = relationship(
        secondary=role_permissions,
        back_populates="permissions"
    )

class Role(Base, BaseModelMixin):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True) # e.g. "Admin", "Manager", "Employee"
    description: Mapped[str] = mapped_column(String(255), nullable=True)

    # Relationships
    permissions: Mapped[List[Permission]] = relationship(
        secondary=role_permissions,
        back_populates="roles",
        lazy="selectin"
    )
    users: Mapped[List["User"]] = relationship(
        secondary="user_roles",
        back_populates="roles"
    )
