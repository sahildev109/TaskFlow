from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.models.user import User, UserRole
from app.schemas.user import UserRegister, TokenResponse
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token
)
from app.core.config import settings
from app.db.redis import blacklist_token, is_token_blacklisted
from app.core.logging import app_logger


async def register_user(payload: UserRegister, db: AsyncSession) -> User:
    # Check email uniqueness
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Check username uniqueness
    existing_username = await db.execute(
        select(User).where(User.username == payload.username)
    )
    if existing_username.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )

    user = User(
        email=payload.email,
        username=payload.username,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=UserRole.USER,
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    app_logger.info(f"New user registered: {user.email}")
    return user


async def login_user(email: str, password: str, db: AsyncSession) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    access_token = create_access_token(str(user.id), user.role)
    refresh_token = create_refresh_token(str(user.id))
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    app_logger.info(f"User logged in: {user.email}")
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=expires_in,
    )


async def refresh_access_token(refresh_token: str, db: AsyncSession) -> dict:
    payload = decode_token(refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    new_access_token = create_access_token(str(user.id), user.role)
    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


async def logout_user(token: str):
    payload = decode_token(token)
    if payload:
        user_id = payload.get("sub")
        issued_at = payload.get("iat", "")
        exp = payload.get("exp", 0)
        jti = f"{user_id}:{issued_at}"
        import time
        ttl = max(0, int(exp - time.time()))
        await blacklist_token(jti, ttl)
        app_logger.info(f"User {user_id} logged out, token blacklisted")
