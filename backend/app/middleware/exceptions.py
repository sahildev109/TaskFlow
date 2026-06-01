from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError
from app.core.logging import app_logger


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({"field": field, "message": error["msg"]})
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "Validation failed",
            "detail": errors,
            "status_code": 422,
        },
    )


async def integrity_error_handler(request: Request, exc: IntegrityError):
    app_logger.error(f"DB integrity error on {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "success": False,
            "error": "Database conflict",
            "detail": "A record with this data already exists",
            "status_code": 409,
        },
    )


async def generic_exception_handler(request: Request, exc: Exception):
    app_logger.error(f"Unhandled exception on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": "An unexpected error occurred",
            "status_code": 500,
        },
    )
