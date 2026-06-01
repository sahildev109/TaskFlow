import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import app_logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = (time.perf_counter() - start_time) * 1000

        app_logger.info(
            f"{request.method} {request.url.path} "
            f"→ {response.status_code} "
            f"[{process_time:.2f}ms]"
        )
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
        return response
