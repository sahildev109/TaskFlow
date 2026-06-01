import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator, ConfigDict
from app.models.task import TaskStatus, TaskPriority


# ── Request Schemas ───────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None

    @field_validator("title")
    @classmethod
    def sanitize_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Title cannot be empty")
        if len(v) > 200:
            raise ValueError("Title cannot exceed 200 characters")
        return v

    @field_validator("description")
    @classmethod
    def sanitize_description(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return v.strip()[:5000]
        return v


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None

    @field_validator("title")
    @classmethod
    def sanitize_title(cls, v: Optional[str]) -> Optional[str]:
        if v:
            v = v.strip()
            if not v:
                raise ValueError("Title cannot be empty")
            if len(v) > 200:
                raise ValueError("Title cannot exceed 200 characters")
        return v


# ── Response Schemas ──────────────────────────────────────────────────────────

class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    due_date: Optional[datetime]
    owner_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class TaskListResponse(BaseModel):
    tasks: list[TaskResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ── Query Filter Schema ───────────────────────────────────────────────────────

class TaskFilter(BaseModel):
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    search: Optional[str] = None
    page: int = 1
    page_size: int = 20

    @field_validator("page")
    @classmethod
    def validate_page(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Page must be >= 1")
        return v

    @field_validator("page_size")
    @classmethod
    def validate_page_size(cls, v: int) -> int:
        if v < 1 or v > 100:
            raise ValueError("Page size must be between 1 and 100")
        return v
