import uuid
from datetime import datetime
from typing import Optional

from app.schemas.user import UserResponse
from app.validators.auth_validators import sanitize_string
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)

    @field_validator("name", "description")
    @classmethod
    def clean_fields(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return sanitize_string(v)
        return v


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)

    @field_validator("name", "description")
    @classmethod
    def clean_fields(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return sanitize_string(v)
        return v


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: Optional[str] = None
    owner_id: uuid.UUID
    owner: UserResponse
    created_at: datetime
    updated_at: datetime
