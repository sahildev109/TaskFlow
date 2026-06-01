from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.user import (
    UserRegister, UserLogin, UserResponse,
    TokenResponse, RefreshTokenRequest, AccessTokenResponse
)
from app.schemas.common import SuccessResponse
from app.services import auth_service
from app.api.v1.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])
bearer_scheme = HTTPBearer(auto_error=True)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Creates a new user account with USER role. Password must be min 8 chars, contain uppercase and digit.",
)
async def register(payload: UserRegister, db: AsyncSession = Depends(get_db)):
    user = await auth_service.register_user(payload, db)
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and get JWT tokens",
    description="Authenticates user credentials and returns access + refresh token pair.",
)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    return await auth_service.login_user(payload.email, payload.password, db)


@router.post(
    "/refresh",
    response_model=AccessTokenResponse,
    summary="Refresh access token",
    description="Exchange a valid refresh token for a new access token.",
)
async def refresh_token(
    payload: RefreshTokenRequest, db: AsyncSession = Depends(get_db)
):
    return await auth_service.refresh_access_token(payload.refresh_token, db)


@router.post(
    "/logout",
    response_model=SuccessResponse,
    summary="Logout and invalidate token",
    description="Blacklists the current access token in Redis. Token will be rejected until it expires.",
)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    current_user: User = Depends(get_current_user),
):
    await auth_service.logout_user(credentials.credentials)
    return SuccessResponse(message="Successfully logged out")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Returns the authenticated user's profile information.",
)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
