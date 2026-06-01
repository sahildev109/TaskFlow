import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.v1.deps import get_current_user, require_admin
from app.models.user import User
from app.schemas.user import UserResponse, UserListResponse, UserUpdate, AdminUserUpdate
from app.schemas.common import SuccessResponse
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Users"])


# ── Current User ──────────────────────────────────────────────────────────────

@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update own profile",
)
async def update_my_profile(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await user_service.update_profile(current_user.id, payload, db)


# ── Admin Routes ──────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=dict,
    summary="[Admin] List all users",
    description="Paginated list of all registered users. Requires ADMIN role.",
)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await user_service.list_users(page, page_size, db)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="[Admin] Get user by ID",
)
async def get_user(
    user_id: uuid.UUID,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await user_service.get_user_by_id(user_id, db)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="[Admin] Update any user (including role and active status)",
)
async def admin_update_user(
    user_id: uuid.UUID,
    payload: AdminUserUpdate,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await user_service.admin_update_user(user_id, payload, db)


@router.delete(
    "/{user_id}",
    response_model=SuccessResponse,
    summary="[Admin] Deactivate a user account",
)
async def deactivate_user(
    user_id: uuid.UUID,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    await user_service.delete_user(user_id, db)
    return SuccessResponse(message="User deactivated successfully")
