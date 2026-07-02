from typing import List, Optional
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import BaseModelMixin
from app.models.association import user_roles, task_assignments
from app.models.role import Role

class User(Base, BaseModelMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Relationships
    roles: Mapped[List[Role]] = relationship(
        secondary=user_roles,
        back_populates="users",
        lazy="selectin"
    )
    owned_projects: Mapped[List["Project"]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan"
    )
    assigned_tasks: Mapped[List["Task"]] = relationship(
        secondary=task_assignments,
        back_populates="assignees"
    )
    comments: Mapped[List["Comment"]] = relationship(
        back_populates="author",
        cascade="all, delete-orphan"
    )
