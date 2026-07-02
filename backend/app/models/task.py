import enum
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, ForeignKey, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import BaseModelMixin
from app.models.association import task_assignments

class TaskStatus(str, enum.Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    REVIEW = "REVIEW"
    DONE = "DONE"

class TaskPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class Task(Base, BaseModelMixin):
    __tablename__ = "tasks"

    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(2000), nullable=True)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="task_status_enum"),
        default=TaskStatus.TODO,
        nullable=False,
        index=True
    )
    priority: Mapped[TaskPriority] = mapped_column(
        Enum(TaskPriority, name="task_priority_enum"),
        default=TaskPriority.MEDIUM,
        nullable=False,
        index=True
    )
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="tasks")
    assignees: Mapped[List["User"]] = relationship(
        secondary=task_assignments,
        back_populates="assigned_tasks",
        lazy="selectin"
    )
    comments: Mapped[List["Comment"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan"
    )
