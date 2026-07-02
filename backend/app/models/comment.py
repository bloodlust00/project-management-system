from typing import TYPE_CHECKING

from app.core.database import Base
from app.models.base import BaseModelMixin
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.task import Task
    from app.models.user import User


class Comment(Base, BaseModelMixin):
    __tablename__ = "comments"

    content: Mapped[str] = mapped_column(String(1000), nullable=False)
    task_id: Mapped[UUID] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    author_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    task: Mapped["Task"] = relationship(back_populates="comments")
    author: Mapped["User"] = relationship(back_populates="comments", lazy="selectin")
