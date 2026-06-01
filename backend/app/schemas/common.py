from typing import Any, Optional
from pydantic import BaseModel


class SuccessResponse(BaseModel):
    success: bool = True
    message: str
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[Any] = None
    status_code: int


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    redis: str
    environment: str
