import os
from typing import List, Union
from pydantic import AnyHttpUrl, BeforeValidator, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Annotated

def any_http_url_to_str(v: Union[str, AnyHttpUrl]) -> str:
    if isinstance(v, AnyHttpUrl):
        return str(v)
    return v

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )

    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Project Management System API"

    # CORS configuration
    BACKEND_CORS_ORIGINS: Annotated[
        List[str], BeforeValidator(lambda v: [x.strip() for x in v.split(",")] if isinstance(v, str) else v)
    ] = ["http://localhost", "http://127.0.0.1", "http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]

    # Security & JWT
    SECRET_KEY: str = "SUPER_SECRET_REPLACE_ME_IN_PRODUCTION_JWT_SECRET_KEY_12345"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "pms"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str | None = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str | None, info) -> str:
        if isinstance(v, str) and v:
            return v
        data = info.data
        server = data.get("POSTGRES_SERVER")
        user = data.get("POSTGRES_USER")
        password = data.get("POSTGRES_PASSWORD")
        db = data.get("POSTGRES_DB")
        port = data.get("POSTGRES_PORT", 5432)
        # Using asyncpg driver for async SQLAlchemy operations
        return f"postgresql+asyncpg://{user}:{password}@{server}:{port}/{db}"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None

    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # Initial Admin Seeding
    INITIAL_ADMIN_EMAIL: str = "admin@example.com"
    INITIAL_ADMIN_PASSWORD: str = "Admin@1234!"

settings = Settings()
