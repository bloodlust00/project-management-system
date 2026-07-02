from typing import List
from sqlalchemy import String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import BaseModelMixin

class Project(Base, BaseModelMixin):
    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(1000), nullable=True)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    owner: Mapped["User"] = relationship(back_populates="owned_projects")
    tasks: Mapped[List["Task"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan"
    )
