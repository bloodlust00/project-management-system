import uuid
from datetime import datetime
from typing import List, Optional

from app.schemas.role import RoleResponse
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str
    is_active: bool
    avatar_url: Optional[str] = None
    roles: List[RoleResponse] = []
    created_at: datetime
    updated_at: datetime


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    avatar_url: Optional[str] = None
    is_active: Optional[bool] = None


class UserUpdateRoles(BaseModel):
    role_names: List[str] = Field(..., description="List of role names to assign to the user.")


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=100)
    role_names: List[str] = Field(default=["Employee"], description="List of role names to associate on creation.")
