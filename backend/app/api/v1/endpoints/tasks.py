import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.task import TaskStatus, TaskPriority
from app.schemas.task import (
    TaskCreate, TaskUpdate, TaskResponse, TaskListResponse, TaskFilter
)
from app.schemas.common import SuccessResponse
from app.services import task_service

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post(
    "/",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
)
async def create_task(
    payload: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await task_service.create_task(payload, current_user, db)


@router.get(
    "/",
    response_model=TaskListResponse,
    summary="List tasks with filters and pagination",
    description="Returns paginated task list. Users see their own tasks; admins see all.",
)
async def list_tasks(
    status: Optional[TaskStatus] = Query(None),
    priority: Optional[TaskPriority] = Query(None),
    search: Optional[str] = Query(None, max_length=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    filters = TaskFilter(
        status=status,
        priority=priority,
        search=search,
        page=page,
        page_size=page_size,
    )
    return await task_service.list_tasks(filters, current_user, db)


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get a task by ID",
)
async def get_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await task_service.get_task(task_id, current_user, db)


@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update a task (partial update)",
    description="PATCH supports partial updates. Only provided fields are changed.",
)
async def update_task(
    task_id: uuid.UUID,
    payload: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await task_service.update_task(task_id, payload, current_user, db)


@router.delete(
    "/{task_id}",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Soft-delete a task",
    description="Marks task as deleted (soft delete). Data is retained in DB.",
)
async def delete_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await task_service.delete_task(task_id, current_user, db)
    return SuccessResponse(message="Task deleted successfully")
