import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.user import UserUpdate, AdminUserUpdate
from app.core.security import hash_password
from app.core.logging import app_logger


async def get_user_by_id(user_id: uuid.UUID, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


async def list_users(page: int, page_size: int, db: AsyncSession) -> dict:
    count_result = await db.execute(select(func.count(User.id)))
    total = count_result.scalar()

    offset = (page - 1) * page_size
    result = await db.execute(
        select(User).order_by(User.created_at.desc()).offset(offset).limit(page_size)
    )
    users = result.scalars().all()

    return {
        "users": users,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


async def update_profile(
    user_id: uuid.UUID, payload: UserUpdate, db: AsyncSession
) -> User:
    user = await get_user_by_id(user_id, db)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    await db.flush()
    await db.refresh(user)
    app_logger.info(f"User profile updated: {user_id}")
    return user


async def admin_update_user(
    user_id: uuid.UUID, payload: AdminUserUpdate, db: AsyncSession
) -> User:
    user = await get_user_by_id(user_id, db)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    await db.flush()
    await db.refresh(user)
    app_logger.info(f"Admin updated user: {user_id}")
    return user


async def delete_user(user_id: uuid.UUID, db: AsyncSession) -> None:
    user = await get_user_by_id(user_id, db)
    user.is_active = False
    await db.flush()
    app_logger.info(f"User deactivated: {user_id}")
