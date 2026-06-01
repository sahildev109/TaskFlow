import json
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from fastapi import HTTPException, status
from app.models.task import Task
from app.models.user import User, UserRole
from app.schemas.task import TaskCreate, TaskUpdate, TaskFilter, TaskListResponse, TaskResponse
from app.db.redis import cache_set, cache_get, cache_delete, cache_delete_pattern
from app.core.logging import app_logger


CACHE_TTL = 120  # 2 minutes


def _task_cache_key(user_id: str, task_id: str) -> str:
    return f"task:{user_id}:{task_id}"


def _task_list_cache_key(user_id: str) -> str:
    return f"tasks:{user_id}:*"


async def create_task(payload: TaskCreate, owner: User, db: AsyncSession) -> Task:
    task = Task(
        title=payload.title,
        description=payload.description,
        status=payload.status,
        priority=payload.priority,
        due_date=payload.due_date,
        owner_id=owner.id,
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)

    # Bust list cache
    await cache_delete_pattern(f"tasks:{owner.id}:*")
    app_logger.info(f"Task created: {task.id} by user {owner.id}")
    return task


async def get_task(
    task_id: uuid.UUID, current_user: User, db: AsyncSession
) -> Task:
    cache_key = _task_cache_key(str(current_user.id), str(task_id))
    cached = await cache_get(cache_key)
    if cached:
        data = json.loads(cached)
        return data  # Return raw dict for response

    query = select(Task).where(Task.id == task_id, Task.is_deleted == False)  # noqa: E712

    # Admins can see all tasks; users only their own
    if current_user.role != UserRole.ADMIN:
        query = query.where(Task.owner_id == current_user.id)

    result = await db.execute(query)
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Cache the result
    task_data = TaskResponse.model_validate(task).model_dump_json()
    await cache_set(cache_key, task_data, CACHE_TTL)
    return task


async def list_tasks(
    filters: TaskFilter, current_user: User, db: AsyncSession
) -> TaskListResponse:
    query = select(Task).where(Task.is_deleted == False)  # noqa: E712

    if current_user.role != UserRole.ADMIN:
        query = query.where(Task.owner_id == current_user.id)

    if filters.status:
        query = query.where(Task.status == filters.status)
    if filters.priority:
        query = query.where(Task.priority == filters.priority)
    if filters.search:
        search_term = f"%{filters.search.strip()}%"
        query = query.where(
            or_(
                Task.title.ilike(search_term),
                Task.description.ilike(search_term),
            )
        )

    # Count total
    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar()

    # Paginate
    offset = (filters.page - 1) * filters.page_size
    query = query.order_by(Task.created_at.desc()).offset(offset).limit(filters.page_size)

    result = await db.execute(query)
    tasks = result.scalars().all()
    total_pages = (total + filters.page_size - 1) // filters.page_size

    return TaskListResponse(
        tasks=[TaskResponse.model_validate(t) for t in tasks],
        total=total,
        page=filters.page,
        page_size=filters.page_size,
        total_pages=total_pages,
    )


async def update_task(
    task_id: uuid.UUID, payload: TaskUpdate, current_user: User, db: AsyncSession
) -> Task:
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.is_deleted == False)  # noqa: E712
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if current_user.role != UserRole.ADMIN and task.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    await db.flush()
    await db.refresh(task)

    # Bust caches
    await cache_delete(_task_cache_key(str(current_user.id), str(task_id)))
    await cache_delete_pattern(f"tasks:{task.owner_id}:*")
    app_logger.info(f"Task updated: {task.id}")
    return task


async def delete_task(
    task_id: uuid.UUID, current_user: User, db: AsyncSession
) -> None:
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.is_deleted == False)  # noqa: E712
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if current_user.role != UserRole.ADMIN and task.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    task.is_deleted = True  # Soft delete
    await db.flush()

    await cache_delete(_task_cache_key(str(current_user.id), str(task_id)))
    await cache_delete_pattern(f"tasks:{task.owner_id}:*")
    app_logger.info(f"Task soft-deleted: {task.id}")
