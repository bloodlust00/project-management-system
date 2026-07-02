from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.db import get_db
from app.services.auth_service import AuthService
from app.schemas.auth import UserRegister, UserLogin, Token, TokenRefresh
from app.schemas.common import APIResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=APIResponse, status_code=201)
async def register(user_in: UserRegister, db: AsyncSession = Depends(get_db)):
    """Registers a new employee account in the system."""
    auth_service = AuthService(db)
    user = await auth_service.register(user_in)
    return APIResponse(
        success=True,
        message="User registered successfully. Default Employee role assigned.",
        data={"user": {"id": str(user.id), "email": user.email, "full_name": user.full_name}}
    )

@router.post("/login", response_model=APIResponse[Token])
async def login(user_login: UserLogin, db: AsyncSession = Depends(get_db)):
    """Authenticates credentials and returns access and refresh token pair (JSON flow)."""
    auth_service = AuthService(db)
    token_data = await auth_service.login(user_login)
    return APIResponse[Token](
        success=True,
        message="Login successful",
        data=Token(**token_data)
    )

@router.post("/swagger-login", include_in_schema=False)
async def swagger_login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """Authenticates credentials from swagger form urlencoded inputs."""
    auth_service = AuthService(db)
    user_login = UserLogin(email=form_data.username, password=form_data.password)
    token_data = await auth_service.login(user_login)
    # Return raw token for oauth2 specs compliance
    return {
        "access_token": token_data["access_token"],
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=APIResponse[Token])
async def refresh(refresh_in: TokenRefresh, db: AsyncSession = Depends(get_db)):
    """Rotates refresh tokens and issues fresh access/refresh token sets."""
    auth_service = AuthService(db)
    rotated_data = await auth_service.rotate_tokens(refresh_in.refresh_token)
    return APIResponse[Token](
        success=True,
        message="Token rotated successfully",
        data=Token(**rotated_data)
    )

@router.post("/logout", response_model=APIResponse)
async def logout(
    refresh_in: TokenRefresh,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Logs out user by blacklisting their access and refresh JWTs."""
    auth_service = AuthService(db)
    
    # Retrieve access token from Auth header if active
    auth_header = request.headers.get("Authorization")
    access_token = None
    if auth_header and auth_header.startswith("Bearer "):
        access_token = auth_header.split(" ")[1]

    await auth_service.logout(
        refresh_token=refresh_in.refresh_token,
        access_token=access_token
    )
    return APIResponse(
        success=True,
        message="User logged out successfully. Tokens blacklisted."
    )
