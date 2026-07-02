import uuid
from datetime import datetime

from app.schemas.user import UserResponse
from app.validators.auth_validators import sanitize_string
from pydantic import BaseModel, ConfigDict, Field, field_validator


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)

    @field_validator("content")
    @classmethod
    def clean_content(cls, v: str) -> str:
        return sanitize_string(v)


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    content: str
    task_id: uuid.UUID
    author_id: uuid.UUID
    author: UserResponse
    created_at: datetime
    updated_at: datetime
