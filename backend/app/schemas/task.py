import uuid
from datetime import datetime
from typing import List, Optional

from app.models.task import TaskPriority, TaskStatus
from app.schemas.user import UserResponse
from app.validators.auth_validators import sanitize_string
from pydantic import BaseModel, ConfigDict, Field, field_validator


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None
    assignee_ids: Optional[List[uuid.UUID]] = Field(
        default=[], description="List of UUIDs representing user assignees."
    )

    @field_validator("title", "description")
    @classmethod
    def clean_fields(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return sanitize_string(v)
        return v


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None
    assignee_ids: Optional[List[uuid.UUID]] = None

    @field_validator("title", "description")
    @classmethod
    def clean_fields(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return sanitize_string(v)
        return v


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: Optional[str] = None
    status: TaskStatus
    priority: TaskPriority
    due_date: Optional[datetime] = None
    project_id: uuid.UUID
    assignees: List[UserResponse] = []
    created_at: datetime
    updated_at: datetime
