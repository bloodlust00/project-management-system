from pydantic import BaseModel, EmailStr, Field, field_validator
from app.validators.auth_validators import validate_password_strength, sanitize_string
from app.schemas.user import UserResponse

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., description="Plain-text password which will be hashed.")
    full_name: str = Field(..., min_length=2, max_length=100)

    @field_validator("password")
    @classmethod
    def check_password(cls, v: str) -> str:
        return validate_password_strength(v)

    @field_validator("full_name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        return sanitize_string(v)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse

class TokenRefresh(BaseModel):
    refresh_token: str

class PasswordChange(BaseModel):
    old_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def check_password(cls, v: str) -> str:
        return validate_password_strength(v)
